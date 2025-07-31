from django import forms
from django.forms import inlineformset_factory
from .models import Campaign, LabTest, Drug, CampaignLabTest, CampaignDrug


class CampaignForm(forms.ModelForm):
    """
    Form for creating and editing campaigns
    """
    class Meta:
        model = Campaign
        fields = [
            'name', 'description', 'start_date', 'end_date', 
            'health_area', 'consent_text', 'status', 'max_patients'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter campaign name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter campaign description'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'health_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter health area/location'
            }),
            'consent_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter consent text that patients will agree to'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'max_patients': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum number of patients (optional)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date must be after start date.")

        return cleaned_data


class CampaignLabTestForm(forms.ModelForm):
    """
    Form for campaign lab tests
    """
    class Meta:
        model = CampaignLabTest
        fields = ['lab_test', 'is_default', 'order']
        widgets = {
            'lab_test': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lab_test'].queryset = LabTest.objects.filter(is_active=True)


class CampaignDrugForm(forms.ModelForm):
    """
    Form for campaign drugs (formulary)
    """
    class Meta:
        model = CampaignDrug
        fields = ['drug', 'is_preferred', 'stock_quantity', 'order']
        widgets = {
            'drug': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_preferred': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Stock quantity (optional)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['drug'].queryset = Drug.objects.filter(is_active=True)


# Formsets for inline editing
CampaignLabTestFormSet = inlineformset_factory(
    Campaign,
    CampaignLabTest,
    form=CampaignLabTestForm,
    extra=1,
    can_delete=True,
    fields=['lab_test', 'is_default', 'order']
)

CampaignDrugFormSet = inlineformset_factory(
    Campaign,
    CampaignDrug,
    form=CampaignDrugForm,
    extra=1,
    can_delete=True,
    fields=['drug', 'is_preferred', 'stock_quantity', 'order']
)


class LabTestForm(forms.ModelForm):
    """
    Form for creating and editing lab tests
    """
    class Meta:
        model = LabTest
        fields = ['name', 'code', 'description', 'category', 'normal_range', 'unit', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter test name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter test code'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter test description'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'normal_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter normal range'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unit of measurement'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class DrugForm(forms.ModelForm):
    """
    Form for creating and editing drugs
    """
    class Meta:
        model = Drug
        fields = ['name', 'generic_name', 'strength', 'dosage_form', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter drug name'
            }),
            'generic_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter generic name'
            }),
            'strength': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter strength (e.g., 500mg)'
            }),
            'dosage_form': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter dosage form (e.g., tablet, capsule)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
