from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # Consultation dashboard and search
    path('', views.consultation_dashboard, name='dashboard'),
    path('search/', views.patient_search_for_consultation, name='patient_search'),
    
    # Consultation management
    path('patient/<int:patient_pk>/new/', views.consultation_create, name='create'),
    path('<int:pk>/', views.consultation_detail, name='detail'),
    path('<int:pk>/edit/', views.consultation_edit, name='edit'),
]
