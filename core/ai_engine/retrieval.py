import os
import time
import logging
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from .config import get_vectorstore

logger = logging.getLogger(__name__)

BACKUP_MODELS = [
    os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free"),  # 1. UTAMA
    "meta-llama/llama-3.3-70b-instruct:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-3-27b-it:free",
]

def ask_bot(user_id, query, request_id: str = "-"):
    """
    RAG: retrieval (filter user) + generation.
    Logic sama seperti sebelumnya, hanya ditambah logging yang lebih informatif.
    """

    t0 = time.time()
    k = 20
    query_preview = query if len(query) <= 140 else query[:140] + "..."

    logger.info(
        "🧠 RAG start user_id=%s k=%s q='%s'",
        user_id, k, query_preview,
        extra={"request_id": request_id},
    )

    # 1) Retriever
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
            "filter": {"user_id": str(user_id)},
        },
    )

    # 2) Prompt
    template = """
    Anda adalah asisten akademik yang teliti. Tugas Anda adalah menganalisis dokumen transkrip/KRS mahasiswa.

    INSTRUKSI:
    1. Baca SEMUA konteks dokumen yang diberikan di bawah ini (dari berbagai semester).
    2. Identifikasi mata kuliah yang nilainya TIDAK LULUS (Biasanya Grade D, E, T, atau Angka < 2.00).
    3. Jika diminta "recap dari awal hingga akhir", urutkan berdasarkan Semester (jika informasinya ada).
    4. Jawablah dengan format List/Daftar yang rapi.

    Konteks Dokumen:
    {context}

    Pertanyaan User: {input}

    Jawaban (Bahasa Indonesia):
    """
    PROMPT = ChatPromptTemplate.from_template(template)

    # 3) Fallback model loop
    last_error = ""
    for idx, model_name in enumerate(BACKUP_MODELS):
        model_t0 = time.time()
        try:
            logger.info(
                "🤖 LLM try idx=%s model=%s",
                idx, model_name,
                extra={"request_id": request_id},
            )

            llm = ChatOpenAI(
                openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
                model_name=model_name,
                temperature=0.1,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AcademicChatbot",
                },
            )

            question_answer_chain = create_stuff_documents_chain(llm, PROMPT)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)

            response = rag_chain.invoke({"input": query})
            answer = response.get("answer", "Maaf, tidak ada jawaban.")

            model_dur = round(time.time() - model_t0, 2)
            total_dur = round(time.time() - t0, 2)

            # Log sukses: model yang dipakai + durasi
            logger.info(
                "✅ LLM ok idx=%s model=%s model_time=%ss total_time=%ss answer_len=%s",
                idx, model_name, model_dur, total_dur, len(answer),
                extra={"request_id": request_id},
            )

            # Kalau bukan model utama, tandai fallback dipakai
            if idx > 0:
                logger.warning(
                    "🛟 Fallback used idx=%s model=%s",
                    idx, model_name,
                    extra={"request_id": request_id},
                )

            return answer

        except Exception as e:
            model_dur = round(time.time() - model_t0, 2)
            last_error = str(e)

            # Potong error biar tidak “banjir”
            err_preview = last_error if len(last_error) <= 200 else last_error[:200] + "..."

            logger.warning(
                "⚠️ LLM fail idx=%s model=%s dur=%ss err=%s",
                idx, model_name, model_dur, err_preview,
                extra={"request_id": request_id},
            )

            if idx < len(BACKUP_MODELS) - 1:
                time.sleep(1)
                continue

            logger.error(
                "❌ All models failed last_err=%s",
                err_preview,
                extra={"request_id": request_id},
                exc_info=True,
            )

    total_dur = round(time.time() - t0, 2)
    return f"Maaf, semua server AI sedang sibuk. (dur={total_dur}s, Error: {last_error})"
