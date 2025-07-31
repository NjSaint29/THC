from .decorators import (
    can_view_demographics, can_edit_demographics,
    can_view_vitals, can_edit_vitals,
    can_view_consultations, can_edit_consultations,
    can_view_lab_results, can_edit_lab_results,
    can_view_prescriptions, can_edit_prescriptions,
    can_register_patients, can_order_lab_tests
)


def user_permissions(request):
    """
    Add user permission checks to template context
    """
    if not request.user.is_authenticated:
        return {}
    
    return {
        'perms': {
            'can_view_demographics': can_view_demographics(request.user),
            'can_edit_demographics': can_edit_demographics(request.user),
            'can_view_vitals': can_view_vitals(request.user),
            'can_edit_vitals': can_edit_vitals(request.user),
            'can_view_consultations': can_view_consultations(request.user),
            'can_edit_consultations': can_edit_consultations(request.user),
            'can_view_lab_results': can_view_lab_results(request.user),
            'can_edit_lab_results': can_edit_lab_results(request.user),
            'can_view_prescriptions': can_view_prescriptions(request.user),
            'can_edit_prescriptions': can_edit_prescriptions(request.user),
            'can_register_patients': can_register_patients(request.user),
            'can_order_lab_tests': can_order_lab_tests(request.user),
        }
    }
