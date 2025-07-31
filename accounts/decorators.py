from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserRole


def role_required(*allowed_roles):
    """
    Decorator to restrict access to specific user roles
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(
                    request, 
                    f'Access denied. This page is only accessible to: {", ".join([role.replace("_", " ").title() for role in allowed_roles])}'
                )
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def registration_clerk_required(view_func):
    """
    Decorator for Registration Clerk only access
    """
    return role_required(UserRole.REGISTRATION_CLERK)(view_func)


def vitals_clerk_required(view_func):
    """
    Decorator for Vitals Clerk only access
    """
    return role_required(UserRole.VITALS_CLERK)(view_func)


def doctor_required(view_func):
    """
    Decorator for Doctor only access
    """
    return role_required(UserRole.DOCTOR)(view_func)


def lab_technician_required(view_func):
    """
    Decorator for Lab Technician only access
    """
    return role_required(UserRole.LAB_TECHNICIAN)(view_func)


def can_view_demographics(user):
    """
    Check if user can view patient demographics
    """
    return user.role in [
        UserRole.REGISTRATION_CLERK,
        UserRole.VITALS_CLERK,
        UserRole.DOCTOR,
        UserRole.LAB_TECHNICIAN,
        UserRole.ADMIN
    ]


def can_edit_demographics(user):
    """
    Check if user can edit patient demographics
    """
    return user.role in [
        UserRole.REGISTRATION_CLERK,
        UserRole.ADMIN
    ]


def can_view_vitals(user):
    """
    Check if user can view clinical parameters
    """
    return user.role in [
        UserRole.VITALS_CLERK,
        UserRole.DOCTOR,
        UserRole.LAB_TECHNICIAN,
        UserRole.ADMIN
    ]


def can_edit_vitals(user):
    """
    Check if user can edit clinical parameters
    """
    return user.role in [
        UserRole.VITALS_CLERK,
        UserRole.ADMIN
    ]


def can_view_consultations(user):
    """
    Check if user can view consultations/diagnosis
    """
    return user.role in [
        UserRole.DOCTOR,
        UserRole.ADMIN
    ]


def can_edit_consultations(user):
    """
    Check if user can edit consultations/diagnosis
    """
    return user.role in [
        UserRole.DOCTOR,
        UserRole.ADMIN
    ]


def can_view_lab_results(user):
    """
    Check if user can view lab results
    """
    return user.role in [
        UserRole.DOCTOR,
        UserRole.LAB_TECHNICIAN,
        UserRole.ADMIN
    ]


def can_edit_lab_results(user):
    """
    Check if user can edit lab results
    """
    return user.role in [
        UserRole.LAB_TECHNICIAN,
        UserRole.ADMIN
    ]


def can_view_prescriptions(user):
    """
    Check if user can view prescriptions
    """
    return user.role in [
        UserRole.DOCTOR,
        UserRole.ADMIN
    ]


def can_edit_prescriptions(user):
    """
    Check if user can edit prescriptions
    """
    return user.role in [
        UserRole.DOCTOR,
        UserRole.ADMIN
    ]


def can_register_patients(user):
    """
    Check if user can register new patients
    """
    return user.role in [
        UserRole.REGISTRATION_CLERK,
        UserRole.ADMIN
    ]


def can_order_lab_tests(user):
    """
    Check if user can order lab tests
    """
    return user.role in [
        UserRole.DOCTOR,
        UserRole.ADMIN
    ]


def section_access_required(section):
    """
    Decorator to enforce section-based access control
    
    Sections:
    - A: Demographics (Registration Clerk)
    - B: Clinical Parameters (Vitals Clerk)
    - C: Medical Consultation (Doctor)
    - D: Laboratory Results (Lab Technician)
    - E: Prescriptions (Doctor)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            section_permissions = {
                'A': [UserRole.REGISTRATION_CLERK, UserRole.ADMIN],
                'B': [UserRole.VITALS_CLERK, UserRole.ADMIN],
                'C': [UserRole.DOCTOR, UserRole.ADMIN],
                'D': [UserRole.LAB_TECHNICIAN, UserRole.ADMIN],
                'E': [UserRole.DOCTOR, UserRole.ADMIN],
            }
            
            allowed_roles = section_permissions.get(section, [])
            
            if user.role not in allowed_roles:
                section_names = {
                    'A': 'Demographics',
                    'B': 'Clinical Parameters',
                    'C': 'Medical Consultation',
                    'D': 'Laboratory Results',
                    'E': 'Prescriptions'
                }
                
                messages.error(
                    request,
                    f'Access denied to {section_names.get(section, "this section")}. '
                    f'Only {", ".join([role.replace("_", " ").title() for role in allowed_roles])} can access this section.'
                )
                return redirect('accounts:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Section-specific decorators
def section_a_required(view_func):
    """Section A: Demographics - Registration Clerk only"""
    return section_access_required('A')(view_func)


def section_b_required(view_func):
    """Section B: Clinical Parameters - Vitals Clerk only"""
    return section_access_required('B')(view_func)


def section_c_required(view_func):
    """Section C: Medical Consultation - Doctor only"""
    return section_access_required('C')(view_func)


def section_d_required(view_func):
    """Section D: Laboratory Results - Lab Technician only"""
    return section_access_required('D')(view_func)


def section_e_required(view_func):
    """Section E: Prescriptions - Doctor only"""
    return section_access_required('E')(view_func)
