from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import LabResult, LabWorksheet, LabOrderWorksheet
from .forms import (
    LabResultForm, LabOrderSearchForm, LabWorksheetForm,
    CriticalValueNotificationForm, LabResultVerificationForm
)
from consultations.models import LabOrder, Consultation
from campaigns.models import LabTest
from accounts.models import UserRole
from patients.models import Patient


@login_required
@permission_required('laboratory.can_enter_lab_results', raise_exception=True)
def lab_dashboard(request):
    """
    Dashboard for lab technicians
    """
    # Get pending lab orders
    pending_orders = LabOrder.objects.filter(
        status__in=['ordered', 'collected']
    ).select_related(
        'consultation__patient', 'lab_test'
    ).order_by('-ordered_date')[:10]

    # Get recent results by this technician
    recent_results = LabResult.objects.filter(
        technician=request.user
    ).select_related(
        'lab_order__consultation__patient', 'lab_order__lab_test'
    ).order_by('-result_date')[:10]

    # Get critical results that need notification
    critical_results = LabResult.objects.filter(
        is_critical=True,
        critical_notified=False,
        status__in=['completed', 'verified']
    ).select_related(
        'lab_order__consultation__patient', 'lab_order__lab_test'
    )[:5]

    # Get statistics
    total_pending = LabOrder.objects.filter(
        status__in=['ordered', 'collected']
    ).count()

    today_results = LabResult.objects.filter(
        technician=request.user,
        result_date__date=timezone.now().date()
    ).count()

    total_results = LabResult.objects.filter(
        technician=request.user
    ).count()

    context = {
        'pending_orders': pending_orders,
        'recent_results': recent_results,
        'critical_results': critical_results,
        'total_pending': total_pending,
        'today_results': today_results,
        'total_results': total_results,
    }

    return render(request, 'laboratory/lab_dashboard.html', context)


@login_required
@permission_required('laboratory.view_labresult', raise_exception=True)
def lab_order_search(request):
    """
    Search interface for lab orders
    """
    lab_orders = []
    search_form = LabOrderSearchForm(request.GET)

    if request.GET.get('search_query') or request.GET.get('status') or request.GET.get('urgency'):
        if search_form.is_valid():
            lab_orders_queryset = LabOrder.objects.select_related(
                'consultation__patient', 'lab_test'
            ).prefetch_related('result')

            search_query = search_form.cleaned_data.get('search_query')
            status = search_form.cleaned_data.get('status')
            urgency = search_form.cleaned_data.get('urgency')
            test_category = search_form.cleaned_data.get('test_category')

            if search_query:
                lab_orders_queryset = lab_orders_queryset.filter(
                    Q(consultation__patient__patient_id__icontains=search_query) |
                    Q(consultation__patient__first_name__icontains=search_query) |
                    Q(consultation__patient__last_name__icontains=search_query) |
                    Q(lab_test__name__icontains=search_query)
                )

            if status:
                lab_orders_queryset = lab_orders_queryset.filter(lab_status=status)

            if urgency:
                lab_orders_queryset = lab_orders_queryset.filter(urgency=urgency)

            if test_category:
                lab_orders_queryset = lab_orders_queryset.filter(lab_test__category=test_category)

            # Pagination
            paginator = Paginator(lab_orders_queryset, 15)
            page_number = request.GET.get('page')
            lab_orders = paginator.get_page(page_number)

    context = {
        'lab_orders': lab_orders,
        'search_form': search_form,
    }

    return render(request, 'laboratory/lab_order_search.html', context)


@login_required
def consultation_lab_results(request, consultation_pk):
    """
    Tabular lab result entry for all tests in a consultation
    """
    # Role-based access control
    if request.user.role not in [UserRole.LAB_TECHNICIAN, UserRole.ADMIN]:
        messages.error(request, 'Access denied. Only lab technicians can enter lab results.')
        return redirect('accounts:dashboard')

    consultation = get_object_or_404(Consultation, pk=consultation_pk)
    lab_orders = consultation.lab_orders.filter(lab_status='ordered').order_by('ordered_date')

    if request.method == 'POST':
        results_saved = 0
        errors = []

        for lab_order in lab_orders:
            result_value = request.POST.get(f'result_value_{lab_order.id}')
            result_unit = request.POST.get(f'result_unit_{lab_order.id}')
            reference_range = request.POST.get(f'reference_range_{lab_order.id}')
            interpretation = request.POST.get(f'interpretation_{lab_order.id}')
            clinical_conclusion = request.POST.get(f'clinical_conclusion_{lab_order.id}')
            is_critical = request.POST.get(f'is_critical_{lab_order.id}') == 'on'

            # Only save if result value is provided
            if result_value and result_value.strip():
                try:
                    # Get or create lab result
                    lab_result, created = LabResult.objects.get_or_create(
                        lab_order=lab_order,
                        defaults={'technician': request.user}
                    )

                    # Update result fields
                    lab_result.result_value = result_value.strip()
                    lab_result.result_unit = result_unit.strip() if result_unit else ''
                    lab_result.reference_range = reference_range.strip() if reference_range else ''
                    lab_result.interpretation = interpretation if interpretation else 'normal'
                    lab_result.clinical_conclusion = clinical_conclusion.strip() if clinical_conclusion else ''
                    lab_result.is_critical = is_critical
                    lab_result.status = 'completed'
                    lab_result.save()

                    # Complete the lab order
                    lab_order.complete_with_results()
                    results_saved += 1

                except Exception as e:
                    errors.append(f'Error saving result for {lab_order.get_test_name()}: {str(e)}')

        if results_saved > 0:
            messages.success(request, f'Successfully saved {results_saved} lab result(s).')

        if errors:
            for error in errors:
                messages.error(request, error)

        # Check if all lab orders for this patient are completed
        patient = consultation.patient
        all_lab_orders = patient.consultations.filter(
            lab_orders__isnull=False
        ).values_list('lab_orders', flat=True)

        if all_lab_orders:
            completed_orders = LabOrder.objects.filter(
                id__in=all_lab_orders,
                lab_status='completed'
            ).count()
            total_orders = len(all_lab_orders)

            if completed_orders == total_orders and patient.status == 'lab_ordered':
                patient.status = 'lab_completed'
                patient.save()
                messages.info(
                    request,
                    f'All lab tests completed for patient {patient.patient_id}. Status updated to Lab Completed.'
                )

        return redirect('laboratory:consultation_lab_results', consultation_pk=consultation.pk)

    # Prepare lab orders with existing results
    lab_orders_with_results = []
    for lab_order in lab_orders:
        try:
            result = lab_order.result
        except LabResult.DoesNotExist:
            result = None

        lab_orders_with_results.append({
            'lab_order': lab_order,
            'result': result
        })

    context = {
        'consultation': consultation,
        'patient': consultation.patient,
        'lab_orders_with_results': lab_orders_with_results,
        'title': f'Lab Results - {consultation.patient.get_full_name()}',
    }

    return render(request, 'laboratory/consultation_lab_results.html', context)


@login_required
def lab_result_entry(request, lab_order_pk):
    """
    Enter lab result for a specific lab order
    """
    # Role-based access control
    if request.user.role not in [UserRole.LAB_TECHNICIAN, UserRole.ADMIN]:
        messages.error(request, 'Access denied. Only lab technicians can enter lab results.')
        return redirect('accounts:dashboard')

    lab_order = get_object_or_404(LabOrder, pk=lab_order_pk)

    try:
        lab_result = lab_order.result
    except LabResult.DoesNotExist:
        lab_result = None

    if request.method == 'POST':
        form = LabResultForm(request.POST, instance=lab_result, lab_order=lab_order)
        if form.is_valid():
            result = form.save(commit=False)
            result.lab_order = lab_order
            if not lab_result:  # New result
                result.technician = request.user
            result.save()

            # Automatically complete lab order when results are saved
            lab_order.complete_with_results()

            # Check if all lab orders for this patient are completed
            patient = lab_order.consultation.patient
            all_lab_orders = patient.consultations.filter(
                lab_orders__isnull=False
            ).values_list('lab_orders', flat=True)

            if all_lab_orders:
                # Use the already imported LabOrder class
                completed_orders = LabOrder.objects.filter(
                    id__in=all_lab_orders,
                    lab_status='completed'  # Use simplified status
                ).count()
                total_orders = len(all_lab_orders)

                # Update patient status if all lab orders are completed
                if completed_orders == total_orders and patient.status == 'lab_ordered':
                    patient.status = 'lab_completed'
                    patient.save()
                    messages.info(
                        request,
                        f'All lab tests completed for patient {patient.patient_id}. Status updated to Lab Completed.'
                    )

            # Success message
            messages.success(
                request,
                f'Lab result for {lab_order.get_test_name()} completed successfully! '
                f'Result is now available to doctors.'
            )

            # Check if critical value notification is needed
            if result.is_critical and not result.critical_notified:
                messages.warning(
                    request,
                    'This is a critical result that requires immediate notification!'
                )
                return redirect('laboratory:critical_notification', result_pk=result.pk)

            return redirect('laboratory:result_detail', pk=result.pk)
    else:
        form = LabResultForm(instance=lab_result, lab_order=lab_order)

    context = {
        'form': form,
        'lab_order': lab_order,
        'lab_result': lab_result,
        'patient': lab_order.consultation.patient,
        'title': f'Enter Result - {lab_order.get_test_name()}',
    }

    return render(request, 'laboratory/lab_result_entry.html', context)


@login_required
@permission_required('laboratory.view_labresult', raise_exception=True)
def lab_result_detail(request, pk):
    """
    Display lab result details
    """
    lab_result = get_object_or_404(
        LabResult.objects.select_related(
            'lab_order__consultation__patient',
            'lab_order__lab_test',
            'technician',
            'verified_by'
        ),
        pk=pk
    )

    context = {
        'lab_result': lab_result,
    }

    return render(request, 'laboratory/lab_result_detail.html', context)


@login_required
@permission_required('laboratory.change_labresult', raise_exception=True)
def critical_value_notification(request, result_pk):
    """
    Handle critical value notification
    """
    lab_result = get_object_or_404(LabResult, pk=result_pk)

    if request.method == 'POST':
        form = CriticalValueNotificationForm(request.POST)
        if form.is_valid():
            # Mark as notified
            lab_result.critical_notified = True
            lab_result.critical_notified_at = form.cleaned_data['notification_time']
            lab_result.save()

            # Log the notification (you could create a separate model for this)
            messages.success(
                request,
                f'Critical value notification recorded for {lab_result.lab_order.consultation.patient.patient_id}'
            )

            return redirect('laboratory:result_detail', pk=lab_result.pk)
    else:
        form = CriticalValueNotificationForm()

    context = {
        'form': form,
        'lab_result': lab_result,
    }

    return render(request, 'laboratory/critical_value_notification.html', context)


@login_required
@permission_required('laboratory.can_verify_lab_results', raise_exception=True)
def lab_result_verification(request, pk):
    """
    Verify lab results (for supervisors)
    """
    lab_result = get_object_or_404(LabResult, pk=pk)

    if request.method == 'POST':
        form = LabResultVerificationForm(request.POST, instance=lab_result)
        if form.is_valid():
            result = form.save(commit=False)
            result.verified_by = request.user
            result.verified_at = timezone.now()
            result.save()

            messages.success(request, 'Lab result verified successfully!')
            return redirect('laboratory:result_detail', pk=result.pk)
    else:
        form = LabResultVerificationForm(instance=lab_result)

    context = {
        'form': form,
        'lab_result': lab_result,
    }

    return render(request, 'laboratory/lab_result_verification.html', context)


@login_required
@permission_required('laboratory.view_labresult', raise_exception=True)
def patient_lab_results(request, patient_pk):
    """
    View all lab results for a specific patient
    """
    patient = get_object_or_404(Patient, pk=patient_pk)

    # Get all lab orders for this patient
    lab_orders = LabOrder.objects.filter(
        consultation__patient=patient
    ).select_related('lab_test').prefetch_related('result').order_by('-ordered_date')

    context = {
        'patient': patient,
        'lab_orders': lab_orders,
    }

    return render(request, 'laboratory/patient_lab_results.html', context)


@login_required
@permission_required('laboratory.add_labworksheet', raise_exception=True)
def worksheet_create(request):
    """
    Create a new lab worksheet
    """
    if request.method == 'POST':
        form = LabWorksheetForm(request.POST)
        if form.is_valid():
            worksheet = form.save(commit=False)
            worksheet.technician = request.user
            worksheet.worksheet_number = worksheet.generate_worksheet_number()
            worksheet.save()

            messages.success(request, f'Worksheet {worksheet.worksheet_number} created successfully!')
            return redirect('laboratory:worksheet_detail', pk=worksheet.pk)
    else:
        form = LabWorksheetForm()

    context = {
        'form': form,
        'title': 'Create New Worksheet',
    }

    return render(request, 'laboratory/worksheet_form.html', context)


@login_required
@permission_required('laboratory.view_labworksheet', raise_exception=True)
def worksheet_detail(request, pk):
    """
    Display worksheet details
    """
    worksheet = get_object_or_404(LabWorksheet, pk=pk)
    lab_orders = worksheet.lab_orders.select_related(
        'lab_order__consultation__patient', 'lab_order__lab_test'
    ).order_by('position')

    context = {
        'worksheet': worksheet,
        'lab_orders': lab_orders,
    }

    return render(request, 'laboratory/worksheet_detail.html', context)


@login_required
def lab_order_ajax_search(request):
    """
    AJAX endpoint for lab order search
    """
    query = request.GET.get('q', '')
    lab_orders = []

    if len(query) >= 2:
        lab_order_queryset = LabOrder.objects.filter(
            Q(consultation__patient__patient_id__icontains=query) |
            Q(consultation__patient__first_name__icontains=query) |
            Q(consultation__patient__last_name__icontains=query) |
            Q(lab_test__name__icontains=query) |
            Q(custom_test_name__icontains=query)
        ).select_related(
            'consultation__patient', 'lab_test'
        )[:10]

        lab_orders = [
            {
                'id': order.pk,
                'patient_id': order.consultation.patient.patient_id,
                'patient_name': order.consultation.patient.get_full_name(),
                'test_name': order.get_test_name(),
                'urgency': order.get_urgency_display(),
                'status': order.get_lab_status_display(),
                'ordered_date': order.ordered_date.strftime('%Y-%m-%d %H:%M'),
                'has_result': hasattr(order, 'result')
            }
            for order in lab_order_queryset
        ]

    return JsonResponse({'lab_orders': lab_orders})


@login_required
@require_http_methods(["POST"])
def update_lab_order_status(request, lab_order_pk):
    """
    AJAX endpoint to update lab order status
    """
    lab_order = get_object_or_404(LabOrder, pk=lab_order_pk)
    new_status = request.POST.get('status')

    if new_status in dict(LabOrder.STATUS_CHOICES):
        lab_order.status = new_status
        lab_order.save()

        return JsonResponse({
            'success': True,
            'message': f'Lab order status updated to {lab_order.get_status_display()}',
            'new_status': new_status,
            'new_status_display': lab_order.get_status_display()
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    })


# Complex status management views removed - simplified to 2-step workflow


@login_required
def lab_order_detail(request, pk):
    """
    View lab order details for technician review
    """
    if request.user.role not in [UserRole.LAB_TECHNICIAN, UserRole.ADMIN]:
        messages.error(request, 'Access denied. Only lab technicians can access this page.')
        return redirect('accounts:dashboard')

    lab_order = get_object_or_404(LabOrder, pk=pk)

    context = {
        'lab_order': lab_order,
        'patient': lab_order.consultation.patient,
        'consultation': lab_order.consultation,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'laboratory/lab_order_detail_modal.html', context)

    return render(request, 'laboratory/lab_order_detail.html', context)
