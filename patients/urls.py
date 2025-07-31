from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Patient management
    path('', views.patient_list, name='list'),
    path('register/', views.patient_register, name='register'),
    path('<int:pk>/', views.patient_detail, name='detail'),
    path('<int:pk>/edit/', views.patient_edit, name='edit'),

    # Vitals/Clinical parameters
    path('vitals/', views.vitals_dashboard, name='vitals_dashboard'),
    path('vitals/search/', views.patient_vitals_search, name='vitals_search'),
    path('<int:patient_pk>/vitals/', views.vitals_entry, name='vitals_entry'),
    path('<int:patient_pk>/vitals/history/', views.vitals_history, name='vitals_history'),

    # AJAX endpoints
    path('search/', views.patient_search_ajax, name='search_ajax'),
]
