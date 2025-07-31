from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    # Prescription management
    path('prescription/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescription/<int:pk>/complete/', views.prescription_complete, name='prescription_complete'),
    path('prescription/<int:pk>/dispense/', views.prescription_dispense, name='prescription_dispense'),
    
    # Dispensing history
    path('dispensing-history/', views.dispensing_history, name='dispensing_history'),
]
