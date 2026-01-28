# core/views.py
import json
import logging
import time

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from inertia import render as inertia_render

# Import Library Auth Django
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.db import IntegrityError  # Untuk handle error username duplikat
from django.contrib import messages  # (tetap dipertahankan walau belum dipakai)

# Import Model & AI Engine
from .models import AcademicDocument, ChatHistory
from .ai_engine.ingest import process_document
from .ai_engine.retrieval import ask_bot

# Inisialisasi Logger
logger = logging.getLogger(__name__)

# ==========================================
# INTERNAL HELPERS (AMAN: tidak mengubah behaviour lain)
# ==========================================

def _rid(request) -> str:
    """Ambil request id dari middleware (kalau ada)."""
    return getattr(request, "request_id", "-")

def _log_extra(request) -> dict:
    """Helper extra untuk logging (agar rid ikut ke formatter)."""
    return {"request_id": _rid(request)}

def _get_client_ip(request):
    """Ambil IP client (support reverse proxy sederhana)."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def _bytes_to_human(n: int) -> str:
    """Konversi bytes → string human readable."""
    try:
        n = int(n)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.2f} {u}" if u != "B" else f"{int(size)} {u}"
        size /= 1024
    return f"{int(n)} B"

def _serialize_documents_for_user(user, limit=50):
    """
    Ambil dokumen user untuk sidebar + hitung total bytes.
    Tidak menambah field baru di model, hanya baca file.size jika tersedia.
    """
    t0 = time.time()

    docs_qs = AcademicDocument.objects.filter(user=user).order_by("-uploaded_at")[:limit]
    documents = []
    total_bytes = 0

    for d in docs_qs:
        size = 0
        try:
            if d.file and hasattr(d.file, "size"):
                size = d.file.size or 0
        except Exception:
            size = 0

        total_bytes += size
        documents.append({
            "id": d.id,
            "title": d.title,
            "is_embedded": d.is_embedded,
            "uploaded_at": d.uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "size_bytes": size,
        })

    dur = round(time.time() - t0, 4)
    logger.debug(
        f"📦 [DOCS SERIALIZE] user={user.username}(id={user.id}) "
        f"count={len(documents)} total={_bytes_to_human(total_bytes)} in {dur}s"
    )
    return documents, total_bytes

def _build_storage_payload(total_bytes: int, quota_bytes: int):
    """Bangun payload storage + percent."""
    quota_bytes = max(int(quota_bytes), 1)
    used_pct = int(min(100, (total_bytes / quota_bytes) * 100))
    return {
        "used_bytes": int(total_bytes),
        "quota_bytes": int(quota_bytes),
        "used_pct": used_pct,
        "used_human": _bytes_to_human(total_bytes),
        "quota_human": _bytes_to_human(quota_bytes),
    }

# ==========================================
# 1. AUTHENTICATION VIEWS (Inertia Edition)
# ==========================================

def register_view(request):
    """Halaman Pendaftaran User Baru via Inertia"""
    if request.user.is_authenticated:
        logger.info(
            f"🔄 [AUTH] User {request.user.username} sudah login -> Redirect Home.",
            extra=_log_extra(request),
        )
        return redirect("home")

    if request.method == "POST":
        ip = _get_client_ip(request)
        try:
            data = json.loads(request.body)

            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            confirm = data.get("password_confirmation")

            errors = {}

            if not username:
                errors["username"] = "Username wajib diisi."
            if not email:
                errors["email"] = "Email wajib diisi."
            if not password:
                errors["password"] = "Password wajib diisi."
            if password != confirm:
                errors["password_confirmation"] = "Password tidak sama."

            if errors:
                logger.warning(
                    f"⚠️ [REGISTER FAIL] ip={ip} validasi_error={errors}",
                    extra=_log_extra(request),
                )
                return inertia_render(request, "Auth/Register", props={"errors": errors})

            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)

            logger.info(
                f"👤 [REGISTER SUCCESS] user={user.username} id={user.id} ip={ip}",
                extra=_log_extra(request),
            )
            return redirect("home")

        except IntegrityError:
            logger.warning(
                f"⚠️ [REGISTER FAIL] ip={ip} username='{username}' sudah terpakai.",
                extra=_log_extra(request),
            )
            return inertia_render(
                request,
                "Auth/Register",
                props={"errors": {"username": "Username sudah digunakan."}},
            )
        except Exception as e:
            logger.error(
                f"❌ [REGISTER ERROR] ip={ip} err={repr(e)}",
                extra=_log_extra(request),
                exc_info=True,
            )
            return inertia_render(
                request,
                "Auth/Register",
                props={"errors": {"auth": "Terjadi kesalahan server."}},
            )

    return inertia_render(request, "Auth/Register")

def login_view(request):
    """Halaman Login User via Inertia"""
    if request.user.is_authenticated:
        logger.info(
            f"🔄 [AUTH] User {request.user.username} sudah login -> Redirect Home.",
            extra=_log_extra(request),
        )
        return redirect("home")

    if request.method == "POST":
        ip = _get_client_ip(request)
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                logger.info(
                    f"🔑 [LOGIN SUCCESS] user={user.username} id={user.id} ip={ip}",
                    extra=_log_extra(request),
                )
                return redirect("home")
            else:
                logger.warning(
                    f"⚠️ [LOGIN FAIL] username={username} ip={ip}",
                    extra=_log_extra(request),
                )
                return inertia_render(
                    request,
                    "Auth/Login",
                    props={"errors": {"auth": "Username atau password salah."}},
                )
        except Exception as e:
            logger.error(
                f"❌ [LOGIN ERROR] ip={ip} err={repr(e)}",
                extra=_log_extra(request),
                exc_info=True,
            )
            return inertia_render(
                request,
                "Auth/Login",
                props={"errors": {"auth": "Error sistem."}},
            )

    return inertia_render(request, "Auth/Login")

def logout_view(request):
    """Logout User"""
    if request.user.is_authenticated:
        user_name = request.user.username
        ip = _get_client_ip(request)
        logout(request)
        logger.info(
            f"🚪 [LOGOUT] user='{user_name}' ip={ip} berhasil keluar.",
            extra=_log_extra(request),
        )
    return redirect("login")

# ==========================================
# 2. INERTIA MAIN VIEW (Dashboard)
# ==========================================

@login_required
def chat_view(request):
    """
    Render Halaman Utama (Dashboard) - Inertia Chat/Index
    Sekarang mengirim props tambahan: documents + storage untuk sidebar.
    """
    t0 = time.time()
    user = request.user
    ip = _get_client_ip(request)

    try:
        logger.info(
            f"🧠 [VIEW START] chat_view user={user.username}(id={user.id}) ip={ip}",
            extra=_log_extra(request),
        )

        # 1) Ambil History Chat
        t_hist = time.time()
        histories = ChatHistory.objects.filter(user=user).order_by("timestamp")
        history_data = [
            {
                "question": h.question,
                "answer": h.answer,
                "time": h.timestamp.strftime("%H:%M"),
                "date": h.timestamp.strftime("%Y-%m-%d"),
            }
            for h in histories
        ]
        hist_dur = round(time.time() - t_hist, 4)
        logger.debug(
            f"💬 [HISTORY FETCH] user={user.username}(id={user.id}) "
            f"count={len(history_data)} in {hist_dur}s"
        )

        # 2) Ambil Documents untuk Sidebar + hitung storage
        documents, total_bytes = _serialize_documents_for_user(user, limit=50)

        # 3) Storage payload (quota contoh 100MB)
        QUOTA_BYTES = 100 * 1024 * 1024
        storage = _build_storage_payload(total_bytes, QUOTA_BYTES)

        props = {
            "user": {"id": user.id, "username": user.username, "email": user.email},
            "initialHistory": history_data,
            "documents": documents,
            "storage": storage,
        }

        total_dur = round(time.time() - t0, 4)
        logger.info(
            f"✅ [VIEW OK] chat_view user={user.username}(id={user.id}) "
            f"hist={len(history_data)} docs={len(documents)} "
            f"storage={storage['used_human']}/{storage['quota_human']}({storage['used_pct']}%) "
            f"in {total_dur}s",
            extra=_log_extra(request),
        )

        return inertia_render(request, "Chat/Index", props=props)

    except Exception as e:
        logger.critical(
            f"❌ [VIEW ERROR] chat_view CRASH user={user.username}(id={user.id}) ip={ip} err={repr(e)}",
            extra=_log_extra(request),
            exc_info=True,
        )
        try:
            return render(request, "500.html")
        except Exception:
            return HttpResponseServerError("500 - Internal Server Error (Cek Terminal)")

# ==========================================
# 3. API ENDPOINTS
# ==========================================

@csrf_exempt
@login_required
def documents_api(request):
    """
    GET /api/documents/
    Endpoint untuk refresh sidebar documents + storage (dipakai frontend setelah upload).
    """
    user = request.user
    ip = _get_client_ip(request)

    if request.method != "GET":
        logger.warning(
            f"⚠️ [DOCS API] Method not allowed method={request.method} user={user.username}(id={user.id}) ip={ip}",
            extra=_log_extra(request),
        )
        return JsonResponse({"status": "error", "msg": "Method not allowed"}, status=405)

    t0 = time.time()
    try:
        documents, total_bytes = _serialize_documents_for_user(user, limit=50)
        QUOTA_BYTES = 100 * 1024 * 1024
        storage = _build_storage_payload(total_bytes, QUOTA_BYTES)

        dur = round(time.time() - t0, 4)
        logger.info(
            f"📄 [DOCS API OK] user={user.username}(id={user.id}) ip={ip} "
            f"docs={len(documents)} storage={storage['used_human']}({storage['used_pct']}%) in {dur}s",
            extra=_log_extra(request),
        )

        return JsonResponse({"documents": documents, "storage": storage})

    except Exception as e:
        dur = round(time.time() - t0, 4)
        logger.error(
            f"❌ [DOCS API ERROR] user={user.username}(id={user.id}) ip={ip} in {dur}s err={repr(e)}",
            extra=_log_extra(request),
            exc_info=True,
        )
        return JsonResponse({"status": "error", "msg": "Terjadi kesalahan server."}, status=500)

@csrf_exempt
@login_required
def upload_api(request):
    """Endpoint Upload File (Batch)"""
    user = request.user
    ip = _get_client_ip(request)

    if request.method == "POST":
        t0 = time.time()
        files = request.FILES.getlist("files")

        if not files:
            logger.warning(
                f"⚠️ [UPLOAD] submit tanpa file user={user.username}(id={user.id}) ip={ip}",
                extra=_log_extra(request),
            )
            return JsonResponse({"status": "error", "msg": "Tidak ada file yang dikirim"}, status=400)

        success_count = 0
        error_count = 0
        errors = []

        logger.info(
            f"📂 [BATCH START] user={user.username}(id={user.id}) ip={ip} files={len(files)}",
            extra=_log_extra(request),
        )

        for index, file_obj in enumerate(files):
            file_size_kb = round(file_obj.size / 1024, 2)
            logger.debug(
                f"➡️ [UPLOAD ITEM] ({index+1}/{len(files)}) name='{file_obj.name}' size={file_size_kb}KB",
                extra=_log_extra(request),
            )

            try:
                doc = AcademicDocument.objects.create(user=user, file=file_obj)
                logger.debug(
                    f"🧾 [DOC CREATED] doc_id={doc.id} title='{doc.title}' path='{doc.file.name}'",
                    extra=_log_extra(request),
                )

                ingest_start = time.time()
                success = process_document(doc)
                ingest_dur = round(time.time() - ingest_start, 3)

                if success:
                    doc.is_embedded = True
                    doc.save(update_fields=["is_embedded"])
                    success_count += 1
                    logger.info(
                        f"✅ [INGEST OK] doc_id={doc.id} file='{file_obj.name}' in {ingest_dur}s",
                        extra=_log_extra(request),
                    )
                else:
                    doc_id = doc.id
                    doc.delete()
                    error_count += 1
                    errors.append(f"{file_obj.name} (Gagal Parsing)")
                    logger.warning(
                        f"⚠️ [INGEST FAIL] doc_id={doc_id} file='{file_obj.name}' in {ingest_dur}s -> deleted",
                        extra=_log_extra(request),
                    )

            except Exception as e:
                error_count += 1
                errors.append(f"{file_obj.name} (System Error)")
                logger.error(
                    f"❌ [SYSTEM ERROR] file='{file_obj.name}' user={user.username}(id={user.id}) err={repr(e)}",
                    extra=_log_extra(request),
                    exc_info=True,
                )

        dur = round(time.time() - t0, 4)
        logger.info(
            f"🏁 [BATCH END] user={user.username}(id={user.id}) ip={ip} "
            f"ok={success_count} fail={error_count} in {dur}s",
            extra=_log_extra(request),
        )

        if success_count > 0:
            msg = f"Berhasil memproses {success_count} file."
            if error_count > 0:
                msg += f" (Gagal: {error_count})"
            return JsonResponse({"status": "success", "msg": msg})
        else:
            return JsonResponse(
                {"status": "error", "msg": f"Gagal semua. Detail: {', '.join(errors)}"},
                status=400,
            )

    logger.warning(
        f"⚠️ [UPLOAD] Method not allowed method={request.method} user={user.username}(id={user.id}) ip={ip}",
        extra=_log_extra(request),
    )
    return JsonResponse({"status": "error", "msg": "Method not allowed"}, status=405)

@csrf_exempt
@login_required
def chat_api(request):
    """Endpoint Chat API"""
    user = request.user
    ip = _get_client_ip(request)

    if request.method == "POST":
        t0 = time.time()
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                logger.warning(
                    f"⚠️ [CHAT] Invalid JSON user={user.username}(id={user.id}) ip={ip}",
                    extra=_log_extra(request),
                )
                return JsonResponse({"error": "Invalid JSON"}, status=400)

            query = data.get("message")
            if not query:
                logger.warning(
                    f"⚠️ [CHAT] Pesan kosong user={user.username}(id={user.id}) ip={ip}",
                    extra=_log_extra(request),
                )
                return JsonResponse({"error": "Pesan kosong"}, status=400)

            q_preview = query if len(query) <= 120 else query[:120] + "..."
            logger.info(
                f"💬 [CHAT REQUEST] user={user.username}(id={user.id}) ip={ip} q='{q_preview}'",
                extra=_log_extra(request),
            )

            # 🔗 Teruskan request_id ke ask_bot agar log retrieval punya rid yang sama
            rid = _rid(request)

            ai_start = time.time()
            answer = ask_bot(user.id, query, request_id=rid)
            ai_dur = round(time.time() - ai_start, 2)

            if not isinstance(answer, str):
                logger.warning(
                    f"⚠️ [CHAT] Non-string answer from AI user={user.username}(id={user.id}) type={type(answer)}",
                    extra=_log_extra(request),
                )
                answer = str(answer)

            logger.info(
                f"🤖 [CHAT RESPONSE] user={user.username}(id={user.id}) ip={ip} ai_time={ai_dur}s len={len(answer)}",
                extra=_log_extra(request),
            )

            ChatHistory.objects.create(user=user, question=query, answer=answer)
            total_dur = round(time.time() - t0, 3)
            logger.debug(
                f"🗃️ [CHAT SAVED] user={user.username}(id={user.id}) total={total_dur}s",
                extra=_log_extra(request),
            )

            return JsonResponse({"answer": answer})

        except Exception as e:
            total_dur = round(time.time() - t0, 3)
            logger.error(
                f"❌ [CHAT CRASH] user={user.username}(id={user.id}) ip={ip} in {total_dur}s err={repr(e)}",
                extra=_log_extra(request),
                exc_info=True,
            )
            return JsonResponse({"error": "Terjadi kesalahan pada server AI."}, status=500)

    logger.warning(
        f"⚠️ [CHAT] Method not allowed method={request.method} user={user.username}(id={user.id}) ip={ip}",
        extra=_log_extra(request),
    )
    return JsonResponse({"status": "error", "msg": "Method not allowed"}, status=405)