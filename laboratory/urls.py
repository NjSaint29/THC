from django.urls import path
from . import views

app_name = 'laboratory'

urlpatterns = [
    # Lab dashboard and search
    path('', views.lab_dashboard, name='dashboard'),
    path('search/', views.lab_order_search, name='lab_order_search'),
    
    # Lab result management
    path('consultation/<int:consultation_pk>/results/', views.consultation_lab_results, name='consultation_lab_results'),
    path('order/<int:lab_order_pk>/result/', views.lab_result_entry, name='result_entry'),
    path('result/<int:pk>/', views.lab_result_detail, name='result_detail'),
    path('result/<int:result_pk>/critical/', views.critical_value_notification, name='critical_notification'),
    path('result/<int:pk>/verify/', views.lab_result_verification, name='result_verification'),
    
    # Patient lab results
    path('patient/<int:patient_pk>/results/', views.patient_lab_results, name='patient_results'),
    
    # Worksheets
    path('worksheet/new/', views.worksheet_create, name='worksheet_create'),
    path('worksheet/<int:pk>/', views.worksheet_detail, name='worksheet_detail'),
    
    # Lab order detail view
    path('order/<int:pk>/', views.lab_order_detail, name='lab_order_detail'),

    # AJAX endpoints
    path('ajax/search/', views.lab_order_ajax_search, name='ajax_search'),
    path('ajax/order/<int:lab_order_pk>/status/', views.update_lab_order_status, name='update_status'),
]
