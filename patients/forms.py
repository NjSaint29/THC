from django import forms
from django.utils import timezone
from .models import Patient, ClinicalParameters
from campaigns.models import Campaign


class PatientRegistrationForm(forms.ModelForm):
    """
    Form for patient registration
    """
    class Meta:
        model = Patient
        fields = [
            'campaign', 'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'age', 'gender', 'marital_status',
            'phone_number', 'email', 'address',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'health_area', 'consent_given'
        ]
        widgets = {
            'campaign': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'required': True
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '150',
                'placeholder': 'Enter age',
                'required': True
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'marital_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter emergency contact phone'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Relationship to patient'
            }),
            'health_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Health area/location'
            }),
            'consent_given': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active campaigns
        self.fields['campaign'].queryset = Campaign.objects.filter(
            status='active'
        ).order_by('name')
        
        # Set health area from campaign if available
        if 'campaign' in self.data:
            try:
                campaign_id = int(self.data.get('campaign'))
                campaign = Campaign.objects.get(id=campaign_id)
                self.fields['health_area'].initial = campaign.health_area
            except (ValueError, Campaign.DoesNotExist):
                pass

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        age = cleaned_data.get('age')
        consent_given = cleaned_data.get('consent_given')

        # Validate age consistency
        if date_of_birth and age:
            today = timezone.now().date()
            calculated_age = today.year - date_of_birth.year
            if today.month < date_of_birth.month or \
               (today.month == date_of_birth.month and today.day < date_of_birth.day):
                calculated_age -= 1
            
            if abs(calculated_age - age) > 1:
                raise forms.ValidationError(
                    "Age and date of birth don't match. Please check your entries."
                )

        # Validate consent
        if not consent_given:
            raise forms.ValidationError(
                "Patient consent is required for registration."
            )

        return cleaned_data

    def save(self, commit=True):
        patient = super().save(commit=False)
        
        # Set consent date if consent is given
        if patient.consent_given:
            patient.consent_date = timezone.now()
        
        # Set health area from campaign if not provided
        if not patient.health_area and patient.campaign:
            patient.health_area = patient.campaign.health_area
        
        if commit:
            patient.save()
        return patient


class ClinicalParametersForm(forms.ModelForm):
    """
    Form for recording clinical parameters/vitals
    """
    class Meta:
        model = ClinicalParameters
        fields = [
            'weight', 'height', 'temperature',
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'glucose_type', 'blood_glucose',
            'lmp', 'is_pregnant', 'gestational_age', 'age_at_first_pregnancy',
            'notes'
        ]
        widgets = {
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Weight in kg'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Height in cm'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Temperature in °C'
            }),
            'systolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Systolic BP (mmHg)'
            }),
            'diastolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Diastolic BP (mmHg)'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Heart rate (bpm)'
            }),
            'glucose_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'blood_glucose': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Blood glucose (mg/dL)'
            }),
            'lmp': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_pregnant': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'gestational_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Gestational age (weeks)'
            }),
            'age_at_first_pregnancy': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age at first pregnancy'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        systolic_bp = cleaned_data.get('systolic_bp')
        diastolic_bp = cleaned_data.get('diastolic_bp')
        is_pregnant = cleaned_data.get('is_pregnant')
        gestational_age = cleaned_data.get('gestational_age')

        # Validate blood pressure
        if systolic_bp and diastolic_bp:
            if systolic_bp <= diastolic_bp:
                raise forms.ValidationError(
                    "Systolic blood pressure must be higher than diastolic blood pressure."
                )

        # Validate pregnancy fields
        if is_pregnant and not gestational_age:
            raise forms.ValidationError(
                "Gestational age is required if patient is pregnant."
            )

        return cleaned_data


class PatientSearchForm(forms.Form):
    """
    Form for searching patients
    """
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by Patient ID, Name, or Phone...'
        })
    )
    
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.all(),
        required=False,
        empty_label="All Campaigns",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Patient.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    gender = forms.ChoiceField(
        choices=[('', 'All Genders')] + Patient.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
