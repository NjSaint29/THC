from django import forms
from django.forms import inlineformset_factory
from .models import Consultation, LabOrder, Prescription
from campaigns.models import LabTest, Drug


class ConsultationForm(forms.ModelForm):
    """
    Form for medical consultations
    """
    class Meta:
        model = Consultation
        fields = [
            'chief_complaint', 'history_of_present_illness',
            'past_medical_history', 'family_history', 'social_history',
            'general_appearance', 'physical_examination',
            'clinical_assessment', 'working_diagnosis', 'treatment_plan',
            'follow_up_instructions', 'referral_needed', 'referral_to', 'referral_reason',
            'status', 'additional_notes'
        ]
        widgets = {
            'chief_complaint': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter the patient\'s main complaint or reason for visit'
            }),
            'history_of_present_illness': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed history of the current illness'
            }),
            'past_medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Previous medical conditions, surgeries, hospitalizations'
            }),
            'family_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Relevant family medical history'
            }),
            'social_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Lifestyle factors, occupation, habits'
            }),
            'general_appearance': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'General appearance and mental state'
            }),
            'physical_examination': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed physical examination findings'
            }),
            'clinical_assessment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Clinical impression and assessment'
            }),
            'working_diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Primary and differential diagnoses'
            }),
            'treatment_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Treatment plan and recommendations'
            }),
            'follow_up_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Follow-up instructions for patient'
            }),
            'referral_needed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'referral_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specialist or facility for referral'
            }),
            'referral_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Reason for referral'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any additional notes or observations'
            }),
        }

    def clean(self):
        # No validation - allow flexible consultation creation
        return super().clean()


class LabOrderForm(forms.ModelForm):
    """
    Form for lab test orders with custom test name support
    """
    # Custom field for test name input
    test_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter lab test name (e.g., Complete Blood Count, Glucose, etc.)'
        }),
        help_text="Enter the name of the laboratory test to be ordered"
    )

    # Optional dropdown for common tests
    common_test = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="Or select from common tests...",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Alternatively, select from commonly ordered tests"
    )

    class Meta:
        model = LabOrder
        fields = ['test_name', 'common_test', 'urgency', 'clinical_indication', 'notes']
        widgets = {
            'urgency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'clinical_indication': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Clinical reason for ordering this test'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign', None)
        super().__init__(*args, **kwargs)

        # Set up common tests dropdown
        if campaign:
            # Filter lab tests to those available in the campaign
            campaign_lab_tests = campaign.lab_tests.values_list('lab_test', flat=True)
            self.fields['common_test'].queryset = LabTest.objects.filter(
                id__in=campaign_lab_tests, is_active=True
            )
        else:
            self.fields['common_test'].queryset = LabTest.objects.filter(is_active=True)

        # If editing existing order, populate the test_name field
        if self.instance and self.instance.pk:
            if self.instance.custom_test_name:
                self.fields['test_name'].initial = self.instance.custom_test_name
            elif self.instance.lab_test:
                self.fields['test_name'].initial = self.instance.lab_test.name
                self.fields['common_test'].initial = self.instance.lab_test

    def clean(self):
        cleaned_data = super().clean()
        test_name = cleaned_data.get('test_name')
        common_test = cleaned_data.get('common_test')

        # If a common test is selected, use its name
        if common_test:
            cleaned_data['test_name'] = common_test.name

        # No validation - allow flexible lab order creation
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle test assignment - allow empty fields
        common_test = self.cleaned_data.get('common_test')
        test_name = self.cleaned_data.get('test_name')

        if common_test:
            # Use formulary test
            instance.lab_test = common_test
            instance.custom_test_name = None
        elif test_name:
            # Use custom test name
            instance.lab_test = None
            instance.custom_test_name = test_name
        else:
            # Allow empty - doctor can fill later
            instance.lab_test = None
            instance.custom_test_name = test_name or ""

        if commit:
            instance.save()
        return instance


class PrescriptionForm(forms.ModelForm):
    """
    Form for prescriptions with custom drug name support
    """
    # Custom field for drug name input
    drug_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter medication name (e.g., Amoxicillin, Paracetamol, etc.)'
        }),
        help_text="Enter the name of the medication to be prescribed"
    )

    # Optional dropdown for common drugs
    common_drug = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="Or select from common medications...",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Alternatively, select from commonly prescribed medications"
    )

    class Meta:
        model = Prescription
        fields = [
            'drug_name', 'common_drug', 'dosage', 'frequency', 'duration', 'route',
            'instructions', 'indication', 'quantity', 'refills', 'notes'
        ]
        widgets = {
            'dosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500mg, 1 tablet, 5ml (can be completed by pharmacy)'
            }),
            'frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., twice daily, every 8 hours, as needed (can be completed by pharmacy)'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 7 days, 2 weeks, until finished (can be completed by pharmacy)'
            }),
            'route': forms.Select(attrs={
                'class': 'form-select'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special instructions for taking the medication'
            }),
            'indication': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What the medication is for'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Total quantity to dispense'
            }),
            'refills': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign', None)
        super().__init__(*args, **kwargs)

        # Set up common drugs dropdown
        if campaign:
            # Filter drugs to those available in the campaign formulary
            campaign_drugs = campaign.formulary.values_list('drug', flat=True)
            self.fields['common_drug'].queryset = Drug.objects.filter(
                id__in=campaign_drugs, is_active=True
            )
        else:
            self.fields['common_drug'].queryset = Drug.objects.filter(is_active=True)

        # If editing existing prescription, populate the drug_name field
        if self.instance and self.instance.pk:
            if self.instance.custom_drug_name:
                self.fields['drug_name'].initial = self.instance.custom_drug_name
            elif self.instance.drug:
                self.fields['drug_name'].initial = self.instance.drug.name
                self.fields['common_drug'].initial = self.instance.drug

    def clean(self):
        cleaned_data = super().clean()
        drug_name = cleaned_data.get('drug_name')
        common_drug = cleaned_data.get('common_drug')

        # If a common drug is selected, use its name
        if common_drug:
            cleaned_data['drug_name'] = common_drug.name

        # No validation - allow flexible prescription creation
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle drug assignment - allow empty fields
        common_drug = self.cleaned_data.get('common_drug')
        drug_name = self.cleaned_data.get('drug_name')

        if common_drug:
            # Use formulary drug
            instance.drug = common_drug
            instance.custom_drug_name = None
        elif drug_name:
            # Use custom drug name
            instance.drug = None
            instance.custom_drug_name = drug_name
        else:
            # Allow empty - doctor can fill later
            instance.drug = None
            instance.custom_drug_name = drug_name or ""

        if commit:
            instance.save()
        return instance


# Simple approach - use standard formsets but modify the view to handle empty forms


# Formsets for inline editing
LabOrderFormSet = inlineformset_factory(
    Consultation,
    LabOrder,
    form=LabOrderForm,
    extra=1,
    can_delete=True,
    fields=['lab_test', 'custom_test_name', 'urgency', 'clinical_indication', 'notes']
)

PrescriptionFormSet = inlineformset_factory(
    Consultation,
    Prescription,
    form=PrescriptionForm,
    extra=1,
    can_delete=True,
    fields=['drug_name', 'common_drug', 'custom_drug_name', 'dosage', 'frequency', 'duration', 'route', 'instructions', 'indication', 'quantity', 'refills', 'notes']
)


class PatientSearchForm(forms.Form):
    """
    Form for searching patients for consultation
    """
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by Patient ID, Name, or Phone...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + [
            ('registered', 'Registered'),
            ('vitals_taken', 'Vitals Taken'),
            ('consultation_done', 'Consultation Done'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
