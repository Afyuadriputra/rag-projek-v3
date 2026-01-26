from django.contrib import admin
from .models import AcademicDocument, ChatHistory

# --- KONFIGURASI HEADER ADMIN ---
admin.site.site_header = "Academic AI Administration"
admin.site.site_title = "Academic Admin Portal"
admin.site.index_title = "Welcome to RAG System Management"

@admin.register(AcademicDocument)
class AcademicDocumentAdmin(admin.ModelAdmin):
    # Kolom yang muncul di tabel daftar
    list_display = ('title', 'user', 'file_link', 'is_embedded', 'uploaded_at')
    
    # Filter sidebar di sebelah kanan
    list_filter = ('is_embedded', 'uploaded_at', 'user')
    
    # Kotak pencarian (bisa cari judul file atau nama user)
    search_fields = ('title', 'user__username', 'user__email')
    
    # Field yang tidak boleh diedit manual (karena otomatis)
    readonly_fields = ('uploaded_at',)

    # Mengelompokkan field saat edit detail
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'file')
        }),
        ('Status System', {
            'fields': ('is_embedded', 'uploaded_at'),
            'description': 'Status apakah file ini sudah diproses oleh AI Engine.'
        }),
    )

    # Helper untuk menampilkan link file yang bisa diklik
    def file_link(self, obj):
        if obj.file:
            return obj.file.name
        return "No File"
    file_link.short_description = "File Path"

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    # Kolom yang muncul (kita potong pertanyaan biar gak kepanjangan)
    list_display = ('user', 'short_question', 'short_answer', 'timestamp')
    
    # Filter berdasarkan user dan waktu
    list_filter = ('timestamp', 'user')
    
    # Search bar (bisa cari isi chattingan)
    search_fields = ('question', 'answer', 'user__username')
    
    # Readonly karena history chat tidak seharusnya diedit admin
    readonly_fields = ('user', 'question', 'answer', 'timestamp')

    # Helper untuk memotong teks pertanyaan yang panjang
    def short_question(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    short_question.short_description = "Question"

    # Helper untuk memotong teks jawaban yang panjang
    def short_answer(self, obj):
        return obj.answer[:50] + "..." if len(obj.answer) > 50 else obj.answer
    short_answer.short_description = "AI Answer"