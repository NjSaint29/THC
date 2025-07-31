from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Consultation, LabOrder, Prescription
from .forms import ConsultationForm, LabOrderFormSet, PrescriptionFormSet, PatientSearchForm
from patients.models import Patient


@login_required
@permission_required('consultations.can_conduct_consultations', raise_exception=True)
def consultation_dashboard(request):
    """
    Dashboard for doctors to manage consultations
    """
    # Get recent consultations by this doctor
    recent_consultations = Consultation.objects.filter(
        doctor=request.user
    ).select_related('patient', 'patient__campaign').order_by('-consultation_date')[:10]

    # Get patients ready for consultation (with vitals taken)
    patients_ready = Patient.objects.filter(
        status='vitals_taken'
    ).select_related('campaign', 'clinical_parameters')[:10]

    # Get statistics
    total_consultations = Consultation.objects.filter(doctor=request.user).count()
    today_consultations = Consultation.objects.filter(
        doctor=request.user,
        consultation_date__date=timezone.now().date()
    ).count()

    pending_consultations = Consultation.objects.filter(
        doctor=request.user,
        status='in_progress'
    ).count()

    context = {
        'recent_consultations': recent_consultations,
        'patients_ready': patients_ready,
        'total_consultations': total_consultations,
        'today_consultations': today_consultations,
        'pending_consultations': pending_consultations,
    }

    return render(request, 'consultations/consultation_dashboard.html', context)


@login_required
@permission_required('consultations.view_consultation', raise_exception=True)
def patient_search_for_consultation(request):
    """
    Search interface for finding patients for consultation
    """
    patients = []
    search_form = PatientSearchForm(request.GET)

    if request.GET.get('search_query') or request.GET.get('status'):
        if search_form.is_valid():
            patients_queryset = Patient.objects.select_related(
                'campaign', 'clinical_parameters'
            ).prefetch_related('consultations')

            search_query = search_form.cleaned_data.get('search_query')
            status = search_form.cleaned_data.get('status')

            if search_query:
                patients_queryset = patients_queryset.filter(
                    Q(patient_id__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(phone_number__icontains=search_query)
                )

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

    return render(request, 'consultations/patient_search.html', context)


@login_required
@permission_required('consultations.add_consultation', raise_exception=True)
def consultation_create(request, patient_pk):
    """
    Create a new consultation for a patient
    """
    patient = get_object_or_404(Patient, pk=patient_pk)

    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        lab_order_formset = LabOrderFormSet(
            request.POST,
            prefix='lab_orders',
            form_kwargs={'campaign': patient.campaign}
        )
        prescription_formset = PrescriptionFormSet(
            request.POST,
            prefix='prescriptions',
            form_kwargs={'campaign': patient.campaign}
        )

        if form.is_valid() and lab_order_formset.is_valid() and prescription_formset.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.doctor = request.user
            consultation.save()

            # Save lab orders
            lab_order_formset.instance = consultation
            lab_orders = lab_order_formset.save()

            # Force create lab orders for forms that have any data but weren't saved
            for form in lab_order_formset.forms:
                if not form.cleaned_data.get('DELETE', False):
                    # Check if any field has data
                    has_data = any([
                        form.cleaned_data.get('test_name'),
                        form.cleaned_data.get('common_test'),
                        form.cleaned_data.get('urgency') != 'routine',  # Default value
                        form.cleaned_data.get('clinical_indication'),
                        form.cleaned_data.get('notes'),
                    ])

                    # Also check raw POST data for this form
                    prefix = form.prefix
                    has_post_data = any([
                        request.POST.get(f'{prefix}-test_name', '').strip(),
                        request.POST.get(f'{prefix}-common_test', '').strip(),
                        request.POST.get(f'{prefix}-urgency', '') not in ['', 'routine'],
                        request.POST.get(f'{prefix}-clinical_indication', '').strip(),
                        request.POST.get(f'{prefix}-notes', '').strip(),
                    ])

                    if (has_data or has_post_data) and not hasattr(form.instance, 'id'):
                        # Create lab order manually since formset didn't save it
                        lab_order = LabOrder(consultation=consultation)

                        # Set fields from cleaned_data or POST data
                        test_name = form.cleaned_data.get('test_name') or request.POST.get(f'{prefix}-test_name', '').strip()
                        common_test = form.cleaned_data.get('common_test')

                        if common_test:
                            lab_order.lab_test = common_test
                            lab_order.custom_test_name = None
                        elif test_name:
                            lab_order.lab_test = None
                            lab_order.custom_test_name = test_name

                        lab_order.urgency = form.cleaned_data.get('urgency') or request.POST.get(f'{prefix}-urgency', 'routine')
                        lab_order.clinical_indication = form.cleaned_data.get('clinical_indication') or request.POST.get(f'{prefix}-clinical_indication', '')
                        lab_order.notes = form.cleaned_data.get('notes') or request.POST.get(f'{prefix}-notes', '')
                        lab_order.lab_status = 'ordered'
                        lab_order.save()
                        lab_orders.append(lab_order)

            # Initialize lab status for each lab order
            for lab_order in lab_orders:
                if not lab_order.lab_status:  # Only set if not already set
                    lab_order.lab_status = 'ordered'
                    lab_order.save()

            # Save prescriptions
            prescription_formset.instance = consultation
            prescriptions = prescription_formset.save()

            # Update pharmacy status for each prescription
            for prescription in prescriptions:
                prescription.update_pharmacy_status()
                prescription.save()

            # Update patient status if consultation is completed
            if consultation.status == 'completed':
                if consultation.lab_orders.exists():
                    patient.status = 'lab_ordered'
                else:
                    patient.status = 'consultation_done'
                patient.save()

            messages.success(
                request,
                f'Consultation for patient {patient.patient_id} saved successfully!'
            )
            return redirect('consultations:detail', pk=consultation.pk)
    else:
        form = ConsultationForm()
        lab_order_formset = LabOrderFormSet(
            prefix='lab_orders',
            form_kwargs={'campaign': patient.campaign}
        )
        prescription_formset = PrescriptionFormSet(
            prefix='prescriptions',
            form_kwargs={'campaign': patient.campaign}
        )

    context = {
        'form': form,
        'lab_order_formset': lab_order_formset,
        'prescription_formset': prescription_formset,
        'patient': patient,
        'title': f'New Consultation - {patient.patient_id}',
    }

    return render(request, 'consultations/consultation_form.html', context)


@login_required
@permission_required('consultations.view_consultation', raise_exception=True)
def consultation_detail(request, pk):
    """
    Display consultation details
    """
    consultation = get_object_or_404(
        Consultation.objects.select_related('patient', 'doctor'),
        pk=pk
    )

    context = {
        'consultation': consultation,
        'lab_orders': consultation.lab_orders.select_related('lab_test').all(),
        'prescriptions': consultation.prescriptions.select_related('drug').all(),
    }

    return render(request, 'consultations/consultation_detail.html', context)


@login_required
@permission_required('consultations.change_consultation', raise_exception=True)
def consultation_edit(request, pk):
    """
    Edit an existing consultation - doctors can only edit consultations they created
    """
    consultation = get_object_or_404(Consultation, pk=pk)
    patient = consultation.patient

    # Check if user can edit this consultation (only if they created it or are admin)
    if request.user.role not in ['admin'] and consultation.doctor != request.user:
        messages.error(request, 'You can only edit consultations that you have created.')
        return redirect('consultations:detail', pk=pk)

    # Only allow the doctor who created the consultation to edit it
    if consultation.doctor != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own consultations.')
        return redirect('consultations:detail', pk=consultation.pk)

    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        lab_order_formset = LabOrderFormSet(
            request.POST,
            instance=consultation,
            prefix='lab_orders',
            form_kwargs={'campaign': patient.campaign}
        )
        prescription_formset = PrescriptionFormSet(
            request.POST,
            instance=consultation,
            prefix='prescriptions',
            form_kwargs={'campaign': patient.campaign}
        )

        if form.is_valid() and lab_order_formset.is_valid() and prescription_formset.is_valid():
            consultation = form.save()

            # Save lab orders and initialize status for new orders
            lab_orders = lab_order_formset.save()
            for lab_order in lab_orders:
                if not lab_order.lab_status:  # Only set if not already set
                    lab_order.lab_status = 'ordered'
                    lab_order.save()

            # Save prescriptions and update pharmacy status
            prescriptions = prescription_formset.save()
            for prescription in prescriptions:
                prescription.update_pharmacy_status()
                prescription.save()

            messages.success(request, 'Consultation updated successfully!')
            return redirect('consultations:detail', pk=consultation.pk)
    else:
        form = ConsultationForm(instance=consultation)
        lab_order_formset = LabOrderFormSet(
            instance=consultation,
            prefix='lab_orders',
            form_kwargs={'campaign': patient.campaign}
        )
        prescription_formset = PrescriptionFormSet(
            instance=consultation,
            prefix='prescriptions',
            form_kwargs={'campaign': patient.campaign}
        )

    context = {
        'form': form,
        'lab_order_formset': lab_order_formset,
        'prescription_formset': prescription_formset,
        'consultation': consultation,
        'patient': patient,
        'title': f'Edit Consultation - {patient.patient_id}',
    }

    return render(request, 'consultations/consultation_form.html', context)
