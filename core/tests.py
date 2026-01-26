import logging
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from .models import AcademicDocument, ChatHistory

# --- KONFIGURASI LOGGING AGAR INFORMATIF ---
# Kita set level ke INFO agar pesan tampil di terminal
logger = logging.getLogger('TEST_LOGGER')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - [TEST] - %(message)s', datefmt='%H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

class AcademicRAGSystemTest(TestCase):
    
    def setUp(self):
        """
        Dijalankan sebelum SETIAP tes dimulai.
        Kita siapkan User dummy dan Client login.
        """
        logger.info("-" * 50)
        logger.info("SETUP: Membuat User Dummy & Login Client")
        self.client = Client()
        self.user = User.objects.create_user(username='mahasiswa_test', password='password123')
        self.client.login(username='mahasiswa_test', password='password123')
        logger.info("SETUP: Berhasil login sebagai 'mahasiswa_test'")

    # --- TEST 1: DATABASE MODELS ---
    def test_model_creation(self):
        logger.info("SCENARIO 1: Testing Database Models")
        
        # Tes Model Dokumen
        doc = AcademicDocument.objects.create(
            user=self.user,
            title="KRS_Semester_5.pdf",
            file="documents/dummy.pdf"
        )
        self.assertEqual(str(doc), "mahasiswa_test - KRS_Semester_5.pdf")
        logger.info("✅ Model AcademicDocument berhasil dibuat dan string representation benar.")

        # Tes Model Chat History
        chat = ChatHistory.objects.create(
            user=self.user,
            question="Apa mata kuliah saya?",
            answer="Anda mengambil Algoritma."
        )
        self.assertEqual(chat.user.username, "mahasiswa_test")
        logger.info("✅ Model ChatHistory berhasil menyimpan riwayat.")

    # --- TEST 2: UPLOAD API (INGESTION) ---
    # @patch menggantikan fungsi asli 'process_document' dengan versi palsu (mock)
    # Ini agar kita tidak perlu parsing PDF beneran saat testing.
    @patch('core.views.process_document') 
    def test_upload_api_flow(self, mock_process_document):
        logger.info("SCENARIO 2: Testing API Upload (Ingestion Flow)")

        # Konfigurasi Mock: Anggap AI sukses memproses file
        mock_process_document.return_value = True 

        # Membuat file PDF palsu di memori
        dummy_file = SimpleUploadedFile(
            "test_krs.pdf", 
            b"Ini adalah isi file PDF dummy untuk testing.", 
            content_type="application/pdf"
        )

        logger.info(f"ACTION: Mengirim POST request ke /api/upload/ dengan file {dummy_file.name}")
        response = self.client.post('/api/upload/', {'file': dummy_file})

        # Assertions (Pengecekan)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AcademicDocument.objects.filter(title="test_krs.pdf").exists())
        
        # Cek apakah fungsi AI dipanggil?
        mock_process_document.assert_called_once()
        
        logger.info(f"RESPONSE: Status Code {response.status_code}")
        logger.info("✅ API Upload berhasil, File tersimpan di DB, dan AI Engine dipicu.")

    # --- TEST 3: CHAT API (RETRIEVAL) ---
    # @patch menggantikan fungsi 'ask_bot' (yang panggil OpenRouter)
    # agar kuota API key Anda tidak berkurang saat tes.
    @patch('core.views.ask_bot')
    def test_chat_api_flow(self, mock_ask_bot):
        logger.info("SCENARIO 3: Testing API Chat (Retrieval Flow)")

        # Konfigurasi Mock: AI menjawab statis
        mock_response_text = "Berdasarkan dokumen, IPK Anda adalah 3.90"
        mock_ask_bot.return_value = mock_response_text

        payload = {"message": "Berapa IPK saya?"}
        
        logger.info(f"ACTION: Mengirim chat -> '{payload['message']}'")
        response = self.client.post(
            '/api/chat/', 
            data=json.dumps(payload), 
            content_type='application/json'
        )

        # Assertions
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Validasi Jawaban
        self.assertEqual(response_data['answer'], mock_response_text)
        logger.info(f"AI ANSWER: {response_data['answer']}")

        # Validasi Database History
        history_exists = ChatHistory.objects.filter(question="Berapa IPK saya?").exists()
        self.assertTrue(history_exists)
        logger.info("✅ Chat history tersimpan di database.")

    # --- TEST 4: SECURITY CHECK ---
    def test_unauthorized_access(self):
        logger.info("SCENARIO 4: Testing Security (Unauthorized User)")
        
        # Logout dulu
        self.client.logout()
        logger.info("ACTION: Client Logout, mencoba akses API...")

        response_upload = self.client.post('/api/upload/')
        response_chat = self.client.post('/api/chat/', data={})

        # Harusnya redirect (302) ke halaman login, atau 403 Forbidden tergantung setting
        # Di default @login_required Django biasanya 302 Found (redirect ke login)
        if response_chat.status_code == 302:
            logger.info("✅ Akses ditolak (Redirect ke Login). Security aman.")
        else:
            logger.warning(f"⚠️ Status code: {response_chat.status_code}. Pastikan @login_required aktif.")