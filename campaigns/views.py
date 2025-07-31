from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Campaign, LabTest, Drug, CampaignLabTest, CampaignDrug
from .forms import CampaignForm, CampaignLabTestFormSet, CampaignDrugFormSet


@login_required
@permission_required('campaigns.view_campaign', raise_exception=True)
def campaign_list(request):
    """
    List all campaigns with filtering and pagination
    """
    campaigns = Campaign.objects.select_related('created_by')

    # Search and filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    health_area_filter = request.GET.get('health_area', '')

    if search_query:
        campaigns = campaigns.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(health_area__icontains=search_query)
        )

    if status_filter:
        campaigns = campaigns.filter(status=status_filter)

    if health_area_filter:
        campaigns = campaigns.filter(health_area__icontains=health_area_filter)

    # Pagination
    paginator = Paginator(campaigns, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unique health areas for filter dropdown
    health_areas = Campaign.objects.values_list('health_area', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'health_area_filter': health_area_filter,
        'health_areas': health_areas,
        'status_choices': Campaign.STATUS_CHOICES,
    }

    return render(request, 'campaigns/campaign_list.html', context)


@login_required
@permission_required('campaigns.view_campaign', raise_exception=True)
def campaign_detail(request, pk):
    """
    Display campaign details
    """
    campaign = get_object_or_404(Campaign, pk=pk)

    context = {
        'campaign': campaign,
        'lab_tests': campaign.lab_tests.select_related('lab_test').order_by('order'),
        'formulary': campaign.formulary.select_related('drug').order_by('order'),
    }

    return render(request, 'campaigns/campaign_detail.html', context)


@login_required
@permission_required('campaigns.add_campaign', raise_exception=True)
def campaign_create(request):
    """
    Create a new campaign
    """
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        lab_test_formset = CampaignLabTestFormSet(request.POST, prefix='lab_tests')
        drug_formset = CampaignDrugFormSet(request.POST, prefix='drugs')

        if form.is_valid() and lab_test_formset.is_valid() and drug_formset.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.save()

            # Save lab tests
            lab_test_formset.instance = campaign
            lab_test_formset.save()

            # Save drugs
            drug_formset.instance = campaign
            drug_formset.save()

            messages.success(request, f'Campaign "{campaign.name}" created successfully!')
            return redirect('campaigns:detail', pk=campaign.pk)
    else:
        form = CampaignForm()
        lab_test_formset = CampaignLabTestFormSet(prefix='lab_tests')
        drug_formset = CampaignDrugFormSet(prefix='drugs')

    context = {
        'form': form,
        'lab_test_formset': lab_test_formset,
        'drug_formset': drug_formset,
        'title': 'Create New Campaign',
    }

    return render(request, 'campaigns/campaign_form.html', context)


@login_required
@permission_required('campaigns.change_campaign', raise_exception=True)
def campaign_edit(request, pk):
    """
    Edit an existing campaign
    """
    campaign = get_object_or_404(Campaign, pk=pk)

    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign)
        lab_test_formset = CampaignLabTestFormSet(
            request.POST, instance=campaign, prefix='lab_tests'
        )
        drug_formset = CampaignDrugFormSet(
            request.POST, instance=campaign, prefix='drugs'
        )

        if form.is_valid() and lab_test_formset.is_valid() and drug_formset.is_valid():
            campaign = form.save()
            lab_test_formset.save()
            drug_formset.save()

            messages.success(request, f'Campaign "{campaign.name}" updated successfully!')
            return redirect('campaigns:detail', pk=campaign.pk)
    else:
        form = CampaignForm(instance=campaign)
        lab_test_formset = CampaignLabTestFormSet(instance=campaign, prefix='lab_tests')
        drug_formset = CampaignDrugFormSet(instance=campaign, prefix='drugs')

    context = {
        'form': form,
        'lab_test_formset': lab_test_formset,
        'drug_formset': drug_formset,
        'campaign': campaign,
        'title': f'Edit Campaign: {campaign.name}',
    }

    return render(request, 'campaigns/campaign_form.html', context)


@login_required
@permission_required('campaigns.delete_campaign', raise_exception=True)
def campaign_delete(request, pk):
    """
    Delete a campaign
    """
    campaign = get_object_or_404(Campaign, pk=pk)

    if request.method == 'POST':
        campaign_name = campaign.name
        campaign.delete()
        messages.success(request, f'Campaign "{campaign_name}" deleted successfully!')
        return redirect('campaigns:list')

    context = {'campaign': campaign}
    return render(request, 'campaigns/campaign_confirm_delete.html', context)


@login_required
@require_http_methods(["POST"])
def campaign_status_update(request, pk):
    """
    AJAX endpoint to update campaign status
    """
    campaign = get_object_or_404(Campaign, pk=pk)
    new_status = request.POST.get('status')

    if new_status in dict(Campaign.STATUS_CHOICES):
        campaign.status = new_status
        campaign.save()

        return JsonResponse({
            'success': True,
            'message': f'Campaign status updated to {campaign.get_status_display()}',
            'new_status': new_status,
            'new_status_display': campaign.get_status_display()
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    })
