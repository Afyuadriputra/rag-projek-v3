from django.urls import path
from . import views

urlpatterns = [
    # --- ROUTES UTAMA ---
    path('', views.chat_view, name='home'),
    
    # --- ROUTES AUTHENTICATION (BARU) ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- API ENDPOINTS ---
    path('api/upload/', views.upload_api, name='upload_api'),
    path('api/chat/', views.chat_api, name='chat_api'),
]