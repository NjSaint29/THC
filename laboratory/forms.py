from django import forms
from django.utils import timezone
from .models import LabResult, LabWorksheet
from consultations.models import LabOrder


class LabResultForm(forms.ModelForm):
    """
    Form for entering laboratory test results
    """
    def __init__(self, *args, **kwargs):
        self.lab_order = kwargs.pop('lab_order', None)
        super().__init__(*args, **kwargs)

        # Pre-populate fields from lab test if available
        if self.lab_order and self.lab_order.lab_test:
            lab_test = self.lab_order.lab_test
            if not self.instance.pk:  # New result
                if hasattr(lab_test, 'normal_range') and lab_test.normal_range:
                    self.fields['reference_range'].initial = lab_test.normal_range
                if hasattr(lab_test, 'unit') and lab_test.unit:
                    self.fields['result_unit'].initial = lab_test.unit

        # Make result_value required
        self.fields['result_value'].required = True

        # Add help text for critical values
        self.fields['is_critical'].help_text = "Check if this result requires immediate physician notification"

    def clean(self):
        cleaned_data = super().clean()
        is_critical = cleaned_data.get('is_critical')
        interpretation = cleaned_data.get('interpretation')
        sample_quality = cleaned_data.get('sample_quality')
        status = cleaned_data.get('status')
        result_value = cleaned_data.get('result_value')

        # Validate that result value is provided
        if not result_value:
            self.add_error('result_value', 'Result value is required.')

        # Validate critical results
        if is_critical and interpretation not in ['critical_low', 'critical_high']:
            self.add_error('interpretation',
                'Critical results must have interpretation of "Critical - Low" or "Critical - High"')

        # Validate sample quality for poor samples
        if sample_quality in ['poor', 'hemolyzed', 'clotted', 'insufficient'] and not cleaned_data.get('technician_notes'):
            self.add_error('technician_notes',
                'Please provide notes explaining the sample quality issue')

        # Validate completed status requirements
        if status in ['completed', 'verified', 'reported']:
            if not interpretation:
                self.add_error('interpretation', 'Interpretation is required for completed results')
            if not cleaned_data.get('reference_range'):
                self.add_error('reference_range', 'Reference range is required for completed results')

        return cleaned_data

    class Meta:
        model = LabResult
        fields = [
            'result_value', 'result_unit', 'reference_range',
            'interpretation', 'sample_quality', 'test_method',
            'technician_notes', 'clinical_conclusion',
            'is_critical', 'status'
        ]
        widgets = {
            'result_value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter the test result value',
                'required': True
            }),
            'result_unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit of measurement (e.g., mg/dL, mmol/L)'
            }),
            'reference_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Normal reference range (e.g., 70-100 mg/dL)'
            }),
            'interpretation': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sample_quality': forms.Select(attrs={
                'class': 'form-select'
            }),
            'test_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Method or equipment used'
            }),
            'technician_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Technical notes about the test procedure or sample'
            }),
            'clinical_conclusion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Clinical interpretation and conclusion'
            }),
            'is_critical': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        lab_order = kwargs.pop('lab_order', None)
        super().__init__(*args, **kwargs)
        
        if lab_order:
            # Pre-populate fields from lab test if available
            lab_test = lab_order.lab_test
            if lab_test and hasattr(lab_test, 'normal_range') and lab_test.normal_range:
                self.fields['reference_range'].initial = lab_test.normal_range
            if lab_test and hasattr(lab_test, 'unit') and lab_test.unit:
                self.fields['result_unit'].initial = lab_test.unit

    def clean(self):
        cleaned_data = super().clean()
        is_critical = cleaned_data.get('is_critical')
        interpretation = cleaned_data.get('interpretation')
        sample_quality = cleaned_data.get('sample_quality')

        # Validate critical results
        if is_critical and interpretation not in ['critical_low', 'critical_high']:
            self.add_error('interpretation', 
                'Critical results must have interpretation of "Critical - Low" or "Critical - High"')

        # Validate sample quality for poor samples
        if sample_quality == 'poor' and not cleaned_data.get('technician_notes'):
            self.add_error('technician_notes', 
                'Please provide notes explaining why the sample quality is poor')

        return cleaned_data


class LabOrderSearchForm(forms.Form):
    """
    Form for searching lab orders
    """
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by Patient ID, Name, or Test...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + LabOrder.LAB_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    urgency = forms.ChoiceField(
        choices=[('', 'All Urgencies')] + [
            ('routine', 'Routine'),
            ('urgent', 'Urgent'),
            ('stat', 'STAT'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    test_category = forms.ChoiceField(
        choices=[('', 'All Categories')] + [
            ('blood', 'Blood Test'),
            ('urine', 'Urine Test'),
            ('stool', 'Stool Test'),
            ('imaging', 'Imaging'),
            ('other', 'Other'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class LabWorksheetForm(forms.ModelForm):
    """
    Form for creating lab worksheets
    """
    class Meta:
        model = LabWorksheet
        fields = ['test_type', 'run_date', 'control_results', 'notes']
        widgets = {
            'test_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'run_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'control_results': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Quality control results for this batch'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default run date to now
        if not self.instance.pk:
            self.fields['run_date'].initial = timezone.now()


class CriticalValueNotificationForm(forms.Form):
    """
    Form for notifying critical values
    """
    notification_method = forms.ChoiceField(
        choices=[
            ('phone', 'Phone Call'),
            ('email', 'Email'),
            ('in_person', 'In Person'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    notified_person = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name of person notified',
            'required': True
        })
    )
    
    notification_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'required': True
        }),
        initial=timezone.now
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes about the notification'
        }),
        required=False
    )


class LabResultVerificationForm(forms.ModelForm):
    """
    Form for verifying lab results (for supervisors)
    """
    class Meta:
        model = LabResult
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    verification_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Verification notes (optional)'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit status choices for verification
        self.fields['status'].choices = [
            ('completed', 'Completed'),
            ('verified', 'Verified'),
            ('reported', 'Reported'),
        ]


class BulkResultEntryForm(forms.Form):
    """
    Form for bulk entry of results from a worksheet
    """
    def __init__(self, *args, **kwargs):
        lab_orders = kwargs.pop('lab_orders', [])
        super().__init__(*args, **kwargs)
        
        for i, lab_order in enumerate(lab_orders):
            # Create fields for each lab order
            self.fields[f'result_value_{lab_order.id}'] = forms.CharField(
                label=f'{lab_order.consultation.patient.patient_id} - {lab_order.lab_test.name}',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter result'
                }),
                required=False
            )
            
            self.fields[f'interpretation_{lab_order.id}'] = forms.ChoiceField(
                choices=[('', '---')] + LabResult.INTERPRETATION_CHOICES,
                widget=forms.Select(attrs={
                    'class': 'form-select'
                }),
                required=False
            )
            
            self.fields[f'notes_{lab_order.id}'] = forms.CharField(
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Notes'
                }),
                required=False
            )
