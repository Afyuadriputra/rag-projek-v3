import os
import time
import logging
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from .config import get_vectorstore

# Inisialisasi Logger
logger = logging.getLogger(__name__)

# =========================================================
# DAFTAR MODEL (FALLBACK STRATEGY)
# =========================================================
BACKUP_MODELS = [
    os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free"),
    # 2. BACKUP 1 
    "xiaomi/mimo-v2-flash:free",
    
    # 3. BACKUP 2 
    "nvidia/nemotron-3-nano-30b-a3b:free",
    
    # 4. BACKUP 3 
    "openai/gpt-oss-120b:free", 
    
    # 5. TERAKHIR 
    "google/gemma-3-27b-it:free",
]

def ask_bot(user_id, query):
    """
    Fungsi RAG dengan Retrieval yang Lebih Luas (High Recall)
    """
    
    # 1. Setup Retriever
    vectorstore = get_vectorstore()
    
    # --- PERUBAHAN PENTING DI SINI ---
    retriever = vectorstore.as_retriever(
        search_type="similarity", # Mencari berdasarkan kemiripan
        search_kwargs={
            'k': 20, # SEBELUMNYA 4. Kita naikkan jadi 20 agar AI baca lebih banyak halaman sekaligus.
            'filter': {'user_id': str(user_id)} 
        }
    )

    # 2. Setup Prompt (Dipertajam untuk rekap nilai)
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

    # 3. LOGIKA LOOPING MODEL (Pantang Menyerah)
    last_error = ""

    for i, model_name in enumerate(BACKUP_MODELS):
        try:
            # Setup LLM
            llm = ChatOpenAI(
                openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
                model_name=model_name,
                temperature=0.1, # Turunkan jadi 0.1 agar lebih faktual/kaku
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AcademicChatbot",
                }
            )

            # Rakit Chain
            question_answer_chain = create_stuff_documents_chain(llm, PROMPT)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)

            response = rag_chain.invoke({"input": query})
            answer = response.get("answer", "Maaf, tidak ada jawaban.")
            
            if i > 0:
                logger.warning(f"✅ SUKSES pakai Backup #{i}: {model_name}")
            
            return answer

        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            logger.warning(f"⚠️ Model {model_name} GAGAL. Error: {error_msg[:100]}...")
            
            if i < len(BACKUP_MODELS) - 1:
                time.sleep(1)
                continue 
            else:
                logger.error("❌ SEMUA MODEL GAGAL.")
                break

    return f"Maaf, semua server AI sedang sibuk. (Error: {last_error})"