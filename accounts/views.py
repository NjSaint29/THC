from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, UserRole
from .forms import CustomLoginForm, PublicStaffRegistrationForm, StaffRegistrationForm, StaffEditForm, RolePermissionForm


def login_view(request):
    """
    Custom login view with role-based redirection
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')

                # Role-based redirection
                next_url = request.GET.get('next', get_dashboard_url_for_role(user.role))
                return redirect(next_url)
            else:
                messages.error(request, 'Your account has been deactivated.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """
    Custom logout view
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    """
    Role-based dashboard view
    """
    user = request.user
    role = user.role

    # Role-specific redirects for complex dashboards
    if role == UserRole.LAB_TECHNICIAN:
        return lab_technician_dashboard(request)
    elif role == UserRole.PHARMACY_CLERK:
        return pharmacy_dashboard(request)

    context = {
        'user': user,
        'role': role,
    }

    # Role-specific dashboard templates for simple dashboards
    template_map = {
        UserRole.ADMIN: 'accounts/dashboards/admin_dashboard.html',
        UserRole.CAMPAIGN_MANAGER: 'accounts/dashboards/campaign_manager_dashboard.html',
        UserRole.REGISTRATION_CLERK: 'accounts/dashboards/registration_clerk_dashboard.html',
        UserRole.VITALS_CLERK: 'accounts/dashboards/vitals_clerk_dashboard.html',
        UserRole.DOCTOR: 'accounts/dashboards/doctor_dashboard.html',
        UserRole.DATA_ANALYST: 'accounts/dashboards/data_analyst_dashboard.html',
    }

    template = template_map.get(role, 'accounts/dashboards/default_dashboard.html')
    return render(request, template, context)


def get_dashboard_url_for_role(role):
    """
    Get the appropriate dashboard URL for a user role
    """
    role_urls = {
        UserRole.ADMIN: 'accounts:admin_dashboard',
        UserRole.CAMPAIGN_MANAGER: 'accounts:campaign_manager_dashboard',
        UserRole.REGISTRATION_CLERK: 'accounts:registration_dashboard',
        UserRole.VITALS_CLERK: 'patients:vitals_dashboard',
        UserRole.DOCTOR: 'consultations:dashboard',
        UserRole.LAB_TECHNICIAN: 'laboratory:dashboard',
        UserRole.PHARMACY_CLERK: 'accounts:pharmacy_dashboard',
        UserRole.DATA_ANALYST: 'accounts:data_analyst_dashboard',
    }

    url_name = role_urls.get(role, 'accounts:dashboard')
    try:
        return reverse(url_name)
    except:
        return reverse('accounts:dashboard')


@login_required
def profile_view(request):
    """
    User profile view
    """
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def admin_dashboard(request):
    """Dashboard for administrators"""
    if request.user.role != UserRole.ADMIN:
        return redirect('accounts:dashboard')

    # Get system statistics
    from django.contrib.auth import get_user_model
    from campaigns.models import Campaign
    from patients.models import Patient
    from consultations.models import Consultation

    User = get_user_model()

    context = {
        'total_users': User.objects.count(),
        'total_campaigns': Campaign.objects.count(),
        'total_patients': Patient.objects.count(),
        'total_consultations': Consultation.objects.count(),
    }

    return render(request, 'accounts/dashboards/admin_dashboard.html', context)


@login_required
def campaign_manager_dashboard(request):
    """Dashboard for campaign managers"""
    if request.user.role != UserRole.CAMPAIGN_MANAGER:
        return redirect('accounts:dashboard')

    return render(request, 'accounts/dashboards/campaign_manager_dashboard.html')


@login_required
def registration_dashboard(request):
    """Dashboard for registration clerks"""
    if request.user.role != UserRole.REGISTRATION_CLERK:
        return redirect('accounts:dashboard')

    return render(request, 'accounts/dashboards/registration_clerk_dashboard.html')


@login_required
def lab_technician_dashboard(request):
    """Dashboard for lab technicians"""
    if request.user.role != UserRole.LAB_TECHNICIAN:
        return redirect('accounts:dashboard')

    from consultations.models import LabOrder
    from django.utils import timezone

    # Get lab orders by simplified status
    ordered_lab_orders = LabOrder.objects.filter(
        lab_status='ordered'
    ).select_related('consultation__patient', 'consultation__doctor', 'consultation', 'lab_test').order_by('-ordered_date')

    completed_today = LabOrder.objects.filter(
        lab_status='completed',
        updated_at__date=timezone.now().date()
    ).select_related('consultation__patient', 'consultation__doctor', 'lab_test').order_by('-updated_at')

    context = {
        'ordered_lab_orders': ordered_lab_orders,
        'completed_today': completed_today,
    }

    return render(request, 'accounts/dashboards/lab_technician_dashboard.html', context)


@login_required
def pharmacy_dashboard(request):
    """Dashboard for pharmacy clerks"""
    if request.user.role != UserRole.PHARMACY_CLERK:
        return redirect('accounts:dashboard')

    from consultations.models import Prescription
    from django.utils import timezone
    from datetime import datetime

    # Get prescriptions by pharmacy status
    pending_prescriptions = Prescription.objects.filter(
        pharmacy_status='pending_review'
    ).select_related('consultation__patient', 'consultation__doctor', 'drug').order_by('-created_at')

    details_needed_prescriptions = Prescription.objects.filter(
        pharmacy_status='details_needed'
    ).select_related('consultation__patient', 'consultation__doctor', 'drug').order_by('-created_at')

    ready_prescriptions = Prescription.objects.filter(
        pharmacy_status='ready_to_dispense'
    ).select_related('consultation__patient', 'consultation__doctor', 'drug').order_by('-created_at')

    # Count dispensed today
    today = timezone.now().date()
    dispensed_today_count = Prescription.objects.filter(
        pharmacy_status='dispensed',
        dispensed_date__date=today
    ).count()

    context = {
        'pending_prescriptions': pending_prescriptions,
        'details_needed_prescriptions': details_needed_prescriptions,
        'ready_prescriptions': ready_prescriptions,
        'dispensed_today_count': dispensed_today_count,
    }

    return render(request, 'accounts/dashboards/pharmacy_dashboard.html', context)


@login_required
def data_analyst_dashboard(request):
    """Dashboard for data analysts"""
    if request.user.role != UserRole.DATA_ANALYST:
        return redirect('accounts:dashboard')

    # Get analytics data
    from patients.models import Patient
    from consultations.models import Consultation
    from laboratory.models import LabResult

    context = {
        'total_patients': Patient.objects.count(),
        'total_consultations': Consultation.objects.count(),
        'total_lab_results': LabResult.objects.count(),
        'total_prescriptions': 0,  # Would be from pharmacy module
    }

    return render(request, 'accounts/dashboards/data_analyst_dashboard.html', context)


@login_required
@permission_required('auth.add_user', raise_exception=True)
def staff_list(request):
    """
    List all staff members with search and filtering
    """
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = User.objects.all().order_by('last_name', 'first_name')

    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)

    context = {
        'users': users_page,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'role_choices': UserRole.choices,
    }

    return render(request, 'accounts/staff_list.html', context)


@login_required
@permission_required('auth.add_user', raise_exception=True)
def staff_register(request):
    """
    Register a new staff member
    """
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Staff member {user.get_full_name()} has been registered successfully!'
            )
            return redirect('accounts:staff_detail', pk=user.pk)
    else:
        form = StaffRegistrationForm()

    context = {
        'form': form,
        'title': 'Register New Staff Member',
    }

    return render(request, 'accounts/staff_register.html', context)


@login_required
@permission_required('auth.view_user', raise_exception=True)
def staff_detail(request, pk):
    """
    View staff member details
    """
    user = get_object_or_404(User, pk=pk)
    role_form = RolePermissionForm(role=user.role)

    context = {
        'staff_user': user,
        'role_info': role_form.get_role_info(),
    }

    return render(request, 'accounts/staff_detail.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
def staff_edit(request, pk):
    """
    Edit staff member details
    """
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Staff member {user.get_full_name()} has been updated successfully!'
            )
            return redirect('accounts:staff_detail', pk=user.pk)
    else:
        form = StaffEditForm(instance=user)

    context = {
        'form': form,
        'staff_user': user,
        'title': f'Edit {user.get_full_name()}',
    }

    return render(request, 'accounts/staff_edit.html', context)


@login_required
@permission_required('auth.delete_user', raise_exception=True)
def staff_deactivate(request, pk):
    """
    Deactivate/reactivate staff member
    """
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.warning(request, f'{user.get_full_name()} has been deactivated.')
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'{user.get_full_name()} has been activated.')

        return redirect('accounts:staff_detail', pk=user.pk)

    context = {
        'staff_user': user,
    }

    return render(request, 'accounts/staff_deactivate.html', context)


@login_required
def role_permissions_view(request):
    """
    View role permissions and descriptions
    """
    role_form = RolePermissionForm()

    context = {
        'role_permissions': role_form.ROLE_PERMISSIONS,
        'role_choices': UserRole.choices,
    }

    return render(request, 'accounts/role_permissions.html', context)


def public_staff_register(request):
    """
    Public staff registration - no login required
    """
    if request.method == 'POST':
        form = PublicStaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Registration successful! Welcome {user.get_full_name()}. '
                f'You can now log in with your credentials as a {user.get_role_display()}.'
            )
            return redirect('accounts:login')
    else:
        form = PublicStaffRegistrationForm()

    context = {
        'form': form,
        'title': 'Staff Registration - Tiko Health Campaign',
    }

    return render(request, 'accounts/public_staff_register.html', context)


def staff_registration_info(request):
    """
    Information page about staff registration
    """
    return render(request, 'accounts/staff_registration_info.html')
