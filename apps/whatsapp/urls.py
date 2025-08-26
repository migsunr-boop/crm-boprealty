from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.webhook_handler, name='whatsapp_webhook_handler'),
    path('webhook/verify/', views.webhook_verify, name='whatsapp_webhook_verify'),
]