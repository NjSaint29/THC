from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    # Campaign management
    path('', views.campaign_list, name='list'),
    path('create/', views.campaign_create, name='create'),
    path('<int:pk>/', views.campaign_detail, name='detail'),
    path('<int:pk>/edit/', views.campaign_edit, name='edit'),
    path('<int:pk>/delete/', views.campaign_delete, name='delete'),
    path('<int:pk>/status/', views.campaign_status_update, name='status_update'),
]
