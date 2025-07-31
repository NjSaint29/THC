from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Role-specific dashboard URLs
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/campaign-manager/', views.campaign_manager_dashboard, name='campaign_manager_dashboard'),
    path('dashboard/registration/', views.registration_dashboard, name='registration_dashboard'),
    path('dashboard/vitals/', views.dashboard_view, name='vitals_dashboard'),  # Redirects to patients app
    path('dashboard/doctor/', views.dashboard_view, name='doctor_dashboard'),  # Redirects to consultations app
    path('dashboard/lab/', views.dashboard_view, name='lab_dashboard'),  # Redirects to laboratory app
    path('dashboard/pharmacy/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('dashboard/data-analyst/', views.data_analyst_dashboard, name='data_analyst_dashboard'),

    # Public staff registration (no login required) - MUST come before admin staff URLs
    path('staff/register/', views.public_staff_register, name='public_staff_register'),
    path('staff/info/', views.staff_registration_info, name='staff_registration_info'),

    # Staff management (admin only)
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/admin/register/', views.staff_register, name='staff_register'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/deactivate/', views.staff_deactivate, name='staff_deactivate'),
    path('roles/', views.role_permissions_view, name='role_permissions'),
]
