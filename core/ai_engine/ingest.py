import pdfplumber
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import get_vectorstore

def process_document(doc_instance):
    """
    Membaca file PDF/Excel/MD, memecahnya, dan menyimpan ke ChromaDB
    dengan Metadata User ID.
    """
    file_path = doc_instance.file.path
    ext = file_path.split('.')[-1].lower()
    text_content = ""

    # 1. PARSING (Ekstraksi Teks)
    try:
        if ext == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Prioritaskan tabel
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            clean_row = [str(item) if item else "" for item in row]
                            text_content += " | ".join(clean_row) + "\n"
                    
                    # Ambil teks narasi biasa
                    text = page.extract_text()
                    if text: text_content += text + "\n"
        
        elif ext in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
            df = df.fillna('') 
            text_content = df.to_markdown(index=False)
            
        elif ext in ['md', 'txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()

        if not text_content.strip():
            return False

        # 2. CHUNKING (Pemecahan Teks)
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_text(text_content)

        if not chunks:
            return False

        # 3. EMBEDDING & STORAGE
        vectorstore = get_vectorstore()
        
        # Metadata User ID
        metadatas = [{"user_id": str(doc_instance.user.id), "source": doc_instance.title} for _ in chunks]
        
        vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        return True

    except Exception as e:
        print(f"Error processing file {doc_instance.title}: {e}")
        return False
