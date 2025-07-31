from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Patient, ClinicalParameters
from .forms import PatientRegistrationForm, ClinicalParametersForm, PatientSearchForm
from campaigns.models import Campaign


@login_required
@permission_required('patients.can_register_patients', raise_exception=True)
def patient_register(request):
    """
    Register a new patient
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.registered_by = request.user
            patient.save()

            # Show success message with patient ID
            messages.success(
                request,
                f'Patient registered successfully! Patient ID: {patient.patient_id}'
            )

            # Return JSON response for AJAX requests (for popup)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'patient_id': patient.patient_id,
                    'patient_name': patient.get_full_name(),
                    'message': f'Patient registered successfully! Patient ID: {patient.patient_id}'
                })

            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientRegistrationForm()

    context = {
        'form': form,
        'title': 'Register New Patient',
        'active_campaigns': Campaign.objects.filter(status='active')
    }

    return render(request, 'patients/patient_register.html', context)


@login_required
def patient_list(request):
    """
    List all patients with search and filtering - accessible to all authenticated users
    """
    patients = Patient.objects.select_related('campaign', 'registered_by')

    # Handle search form
    search_form = PatientSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query')
        campaign = search_form.cleaned_data.get('campaign')
        status = search_form.cleaned_data.get('status')
        gender = search_form.cleaned_data.get('gender')

        if search_query:
            patients = patients.filter(
                Q(patient_id__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        if campaign:
            patients = patients.filter(campaign=campaign)

        if status:
            patients = patients.filter(status=status)

        if gender:
            patients = patients.filter(gender=gender)

    # Pagination
    paginator = Paginator(patients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Role-based permissions for action buttons
    user_permissions = {
        'can_edit_demographics': request.user.role in ['registration_clerk', 'admin'],
        'can_record_vitals': request.user.role in ['vitals_clerk', 'admin'],
        'can_view_details': True,  # All authenticated users can view details
        'can_create_consultation': request.user.role in ['doctor', 'admin'],
        'can_view_lab_results': request.user.role in ['lab_technician', 'doctor', 'admin'],
        'can_view_prescriptions': request.user.role in ['pharmacy_clerk', 'doctor', 'admin'],
        'is_admin': request.user.role == 'admin',
        'is_campaign_manager': request.user.role == 'campaign_manager',
        'is_data_analyst': request.user.role == 'data_analyst',
    }

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'user_permissions': user_permissions,
    }

    return render(request, 'patients/patient_list.html', context)


@login_required
@permission_required('patients.view_patient', raise_exception=True)
def patient_detail(request, pk):
    """
    Display patient details
    """
    patient = get_object_or_404(Patient, pk=pk)

    try:
        clinical_parameters = patient.clinical_parameters
    except ClinicalParameters.DoesNotExist:
        clinical_parameters = None

    context = {
        'patient': patient,
        'clinical_parameters': clinical_parameters,
    }

    return render(request, 'patients/patient_detail.html', context)


@login_required
@permission_required('patients.change_patient', raise_exception=True)
def patient_edit(request, pk):
    """
    Edit patient information - users can only edit patients they registered
    """
    patient = get_object_or_404(Patient, pk=pk)

    # Check if user can edit this patient (only if they registered it or are admin)
    if request.user.role not in ['admin'] and patient.registered_by != request.user:
        messages.error(request, 'You can only edit patients that you have registered.')
        return redirect('patients:detail', pk=pk)

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Patient {patient.patient_id} updated successfully!')
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientRegistrationForm(instance=patient)

    context = {
        'form': form,
        'patient': patient,
        'title': f'Edit Patient: {patient.patient_id}',
    }

    return render(request, 'patients/patient_edit.html', context)


@login_required
def patient_search_ajax(request):
    """
    AJAX endpoint for patient search
    """
    query = request.GET.get('q', '')
    patients = []

    if len(query) >= 2:
        patient_queryset = Patient.objects.filter(
            Q(patient_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:10]

        patients = [
            {
                'id': patient.pk,
                'patient_id': patient.patient_id,
                'name': patient.get_full_name(),
                'age': patient.age,
                'gender': patient.get_gender_display(),
                'campaign': patient.campaign.name,
                'status': patient.get_status_display()
            }
            for patient in patient_queryset
        ]

    return JsonResponse({'patients': patients})


@login_required
@permission_required('patients.add_clinicalparameters', raise_exception=True)
def vitals_entry(request, patient_pk):
    """
    Enter or update patient vitals/clinical parameters
    """
    patient = get_object_or_404(Patient, pk=patient_pk)

    try:
        clinical_parameters = patient.clinical_parameters
    except ClinicalParameters.DoesNotExist:
        clinical_parameters = None

    # Check if user can edit existing vitals (only if they recorded it or are admin)
    if clinical_parameters and request.user.role not in ['admin'] and clinical_parameters.recorded_by != request.user:
        messages.error(request, 'You can only edit vitals that you have recorded.')
        return redirect('patients:detail', pk=patient.pk)

    if request.method == 'POST':
        form = ClinicalParametersForm(request.POST, instance=clinical_parameters)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.patient = patient
            if not clinical_parameters:  # New record
                vitals.recorded_by = request.user
            vitals.save()

            # Update patient status
            if patient.status == 'registered':
                patient.status = 'vitals_taken'
                patient.save()

            messages.success(request, f'Vitals recorded for patient {patient.patient_id}!')
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = ClinicalParametersForm(instance=clinical_parameters)

    context = {
        'form': form,
        'patient': patient,
        'clinical_parameters': clinical_parameters,
        'title': f'Record Vitals: {patient.patient_id}',
    }

    return render(request, 'patients/vitals_entry.html', context)


@login_required
@permission_required('patients.view_clinicalparameters', raise_exception=True)
def vitals_dashboard(request):
    """
    Dashboard for vitals clerks to search and manage patient vitals
    """
    # Get recent patients with vitals
    recent_vitals = ClinicalParameters.objects.select_related(
        'patient', 'patient__campaign', 'recorded_by'
    ).order_by('-updated_at')[:10]

    # Get patients without vitals
    patients_without_vitals = Patient.objects.filter(
        clinical_parameters__isnull=True,
        status='registered'
    ).select_related('campaign')[:10]

    # Get statistics
    total_patients = Patient.objects.count()
    patients_with_vitals = Patient.objects.filter(
        clinical_parameters__isnull=False
    ).count()

    context = {
        'recent_vitals': recent_vitals,
        'patients_without_vitals': patients_without_vitals,
        'total_patients': total_patients,
        'patients_with_vitals': patients_with_vitals,
        'vitals_completion_rate': round((patients_with_vitals / total_patients * 100) if total_patients > 0 else 0, 1),
    }

    return render(request, 'patients/vitals_dashboard.html', context)


@login_required
@permission_required('patients.view_patient', raise_exception=True)
def patient_vitals_search(request):
    """
    Search interface for finding patients to record vitals
    """
    patients = []
    search_form = PatientSearchForm(request.GET)

    if request.GET.get('search_query') or request.GET.get('campaign') or request.GET.get('status'):
        if search_form.is_valid():
            patients_queryset = Patient.objects.select_related('campaign', 'registered_by')

            search_query = search_form.cleaned_data.get('search_query')
            campaign = search_form.cleaned_data.get('campaign')
            status = search_form.cleaned_data.get('status')

            if search_query:
                patients_queryset = patients_queryset.filter(
                    Q(patient_id__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(phone_number__icontains=search_query)
                )

            if campaign:
                patients_queryset = patients_queryset.filter(campaign=campaign)

            if status:
                patients_queryset = patients_queryset.filter(status=status)

            # Pagination
            paginator = Paginator(patients_queryset, 15)
            page_number = request.GET.get('page')
            patients = paginator.get_page(page_number)

    context = {
        'patients': patients,
        'search_form': search_form,
    }

    return render(request, 'patients/vitals_search.html', context)


@login_required
@permission_required('patients.view_clinicalparameters', raise_exception=True)
def vitals_history(request, patient_pk):
    """
    View vitals history for a patient
    """
    patient = get_object_or_404(Patient, pk=patient_pk)

    try:
        clinical_parameters = patient.clinical_parameters
    except ClinicalParameters.DoesNotExist:
        clinical_parameters = None

    context = {
        'patient': patient,
        'clinical_parameters': clinical_parameters,
    }

    return render(request, 'patients/vitals_history.html', context)
