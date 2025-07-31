from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from consultations.models import Prescription
from consultations.forms import PrescriptionForm
from accounts.models import UserRole


@login_required
def prescription_detail(request, pk):
    """
    View prescription details for pharmacy review
    """
    if request.user.role not in [UserRole.PHARMACY_CLERK, UserRole.ADMIN]:
        messages.error(request, 'Access denied. Only pharmacy clerks can access this page.')
        return redirect('accounts:dashboard')

    prescription = get_object_or_404(Prescription, pk=pk)

    context = {
        'prescription': prescription,
        'patient': prescription.consultation.patient,
        'consultation': prescription.consultation,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'pharmacy/prescription_detail_modal.html', context)

    return render(request, 'pharmacy/prescription_detail.html', context)


@login_required
def prescription_complete(request, pk):
    """
    Complete prescription details (dosage, frequency, duration)
    """
    if request.user.role not in [UserRole.PHARMACY_CLERK, UserRole.ADMIN]:
        messages.error(request, 'Access denied. Only pharmacy clerks can complete prescriptions.')
        return redirect('accounts:dashboard')

    prescription = get_object_or_404(Prescription, pk=pk)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            prescription = form.save(commit=False)

            # Update pharmacy status based on completeness
            prescription.update_pharmacy_status()
            prescription.save()

            messages.success(request, f'Prescription details completed for {prescription.get_drug_name()}!')
            return redirect('accounts:pharmacy_dashboard')
    else:
        form = PrescriptionForm(instance=prescription)

    context = {
        'form': form,
        'prescription': prescription,
        'patient': prescription.consultation.patient,
        'title': f'Complete Prescription Details - {prescription.get_drug_name()}',
    }

    return render(request, 'pharmacy/prescription_complete.html', context)


@login_required
@require_http_methods(["POST"])
def prescription_dispense(request, pk):
    """
    Mark prescription as dispensed
    """
    if request.user.role not in [UserRole.PHARMACY_CLERK, UserRole.ADMIN]:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    prescription = get_object_or_404(Prescription, pk=pk)

    if not prescription.is_ready_to_dispense():
        return JsonResponse({
            'success': False,
            'error': 'Prescription is not ready to dispense. Please complete all required details first.'
        })

    # Mark as dispensed
    prescription.pharmacy_status = 'dispensed'
    prescription.status = 'dispensed'
    prescription.dispensed_by = request.user
    prescription.dispensed_date = timezone.now()

    # Set dispensed quantity to prescribed quantity if not specified
    if not prescription.dispensed_quantity and prescription.quantity:
        prescription.dispensed_quantity = prescription.quantity

    prescription.save()

    return JsonResponse({
        'success': True,
        'message': f'Medication {prescription.get_drug_name()} dispensed successfully!'
    })


@login_required
def dispensing_history(request):
    """
    View dispensing history for pharmacy clerks
    """
    if request.user.role not in [UserRole.PHARMACY_CLERK, UserRole.ADMIN]:
        messages.error(request, 'Access denied. Only pharmacy clerks can access this page.')
        return redirect('accounts:dashboard')

    # Get dispensed prescriptions
    dispensed_prescriptions = Prescription.objects.filter(
        pharmacy_status='dispensed'
    ).select_related(
        'consultation__patient',
        'consultation__doctor',
        'drug',
        'dispensed_by'
    ).order_by('-dispensed_date')

    context = {
        'dispensed_prescriptions': dispensed_prescriptions,
    }

    return render(request, 'pharmacy/dispensing_history.html', context)
