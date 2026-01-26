from django.db import models
from django.contrib.auth.models import User
import os

class AcademicDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    # File akan disimpan di media/documents/tahun/bulan/
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_embedded = models.BooleanField(default=False) 

    def save(self, *args, **kwargs):
        # Auto-fill title dari nama file jika kosong
        if not self.title:
            self.title = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp'] # Yang terbaru muncul duluan

    def __str__(self):
        return f"{self.user.username}: {self.question[:20]}..."
