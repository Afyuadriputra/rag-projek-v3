import json
import logging # 1. Import Logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
# Import Library Auth Django
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

# Import Model & AI Engine
from .models import AcademicDocument, ChatHistory
from .ai_engine.ingest import process_document
from .ai_engine.retrieval import ask_bot

# 2. Inisialisasi Logger (CCTV)
logger = logging.getLogger(__name__)

# ==========================================
# 1. AUTHENTICATION VIEWS (Register/Login)
# ==========================================

def register_view(request):
    """Halaman Pendaftaran User Baru"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Selamat datang, {user.username}!")
            logger.info(f"👤 NEW USER: {user.username} berhasil mendaftar.")
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    """Halaman Login User"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info(f"🔑 LOGIN: {user.username} masuk ke sistem.")
                return redirect('home')
            else:
                messages.error(request, "Username atau password salah.")
        else:
            messages.error(request, "Username atau password salah.")
    
    return render(request, 'auth/login.html')

def logout_view(request):
    """Logout User"""
    user_name = request.user.username
    logout(request)
    logger.info(f"🚪 LOGOUT: {user_name} keluar dari sistem.")
    return redirect('login')

# ==========================================
# 2. MAIN APPLICATION VIEWS
# ==========================================

@login_required
def chat_view(request):
    """Render halaman Frontend Chat (Hanya bisa diakses jika login)"""
    return render(request, 'chat/index.html')

# ==========================================
# 3. API ENDPOINTS (AJAX)
# ==========================================

@csrf_exempt
@login_required
@csrf_exempt
@login_required
def upload_api(request):
    """Endpoint untuk upload MULTIPLE file PDF/Excel"""
    # Kita cek apakah ada file dengan key 'files' (jamak)
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        
        success_count = 0
        error_count = 0
        errors = []

        logger.info(f"📂 BATCH UPLOAD: {request.user.username} mencoba upload {len(files)} file.")

        # LOOPING: Proses file satu per satu
        for file_obj in files:
            try:
                # 1. Simpan ke Database Django
                doc = AcademicDocument.objects.create(user=request.user, file=file_obj)
                
                # 2. Proses ke Vector DB (AI Ingestion)
                logger.debug(f"⚙️ Processing: {file_obj.name}")
                success = process_document(doc)
                
                if success:
                    doc.is_embedded = True
                    doc.save()
                    success_count += 1
                else:
                    doc.delete()
                    error_count += 1
                    errors.append(f"{file_obj.name} (Gagal Baca)")
            except Exception as e:
                error_count += 1
                errors.append(f"{file_obj.name} (Error: {str(e)})")
                logger.error(f"❌ Error upload {file_obj.name}: {e}")

        # Buat pesan balasan
        if success_count > 0:
            msg = f"Berhasil memproses {success_count} file."
            if error_count > 0:
                msg += f" Gagal: {error_count} file."
            
            logger.info(f"✅ BATCH SELESAI: {success_count} Sukses, {error_count} Gagal.")
            return JsonResponse({'status': 'success', 'msg': msg})
        else:
            return JsonResponse({'status': 'error', 'msg': f"Semua file gagal diproses. Detail: {', '.join(errors)}"}, status=400)
            
    return JsonResponse({'status': 'error', 'msg': 'Tidak ada file yang dikirim'}, status=400)

@csrf_exempt
@login_required
def chat_api(request):
    """Endpoint untuk Chat Tanya-Jawab"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('message')
            
            if not query:
                return JsonResponse({'error': 'Pesan tidak boleh kosong'}, status=400)

            # LOGGING QUERY
            logger.info(f"💬 CHAT [{request.user.username}]: {query}")

            answer = ask_bot(request.user.id, query)
            
            # LOGGING RESPONSE
            logger.info(f"🤖 AI REPLY: {answer[:50]}...") 
            
            ChatHistory.objects.create(user=request.user, question=query, answer=answer)
            
            return JsonResponse({'answer': answer})
        except Exception as e:
             # LOGGING ERROR
             logger.error(f"❌ CHAT ERROR: {str(e)}", exc_info=True)
             return JsonResponse({'error': str(e)}, status=500)
        
    return JsonResponse({'status': 'error'}, status=400)