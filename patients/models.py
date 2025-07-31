from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from campaigns.models import Campaign
import uuid

User = get_user_model()


class Patient(models.Model):
    """
    Model representing a patient in the health campaign
    """
    # Unique patient identifier
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated unique patient ID (e.g., TIKO-2025-0001)"
    )

    # Campaign association
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='patients'
    )

    # Demographics
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)

    # Personal details
    date_of_birth = models.DateField(blank=True, null=True)
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Age in years"
    )

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        null=True
    )

    # Contact information
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        null=True
    )

    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        null=True
    )
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)

    # Health area (from campaign, but can be overridden)
    health_area = models.CharField(max_length=200)

    # Consent
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(blank=True, null=True)

    # Registration details
    registered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='registered_patients'
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status tracking
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('vitals_taken', 'Vitals Taken'),
        ('consultation_done', 'Consultation Done'),
        ('lab_ordered', 'Lab Tests Ordered'),
        ('lab_completed', 'Lab Tests Completed'),
        ('treatment_completed', 'Treatment Completed'),
        ('discharged', 'Discharged'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered'
    )

    class Meta:
        ordering = ['-registration_date']
        permissions = [
            ('can_register_patients', 'Can register patients'),
            ('can_view_patient_reports', 'Can view patient reports'),
        ]

    def __str__(self):
        return f"{self.patient_id} - {self.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.patient_id:
            self.patient_id = self.generate_patient_id()

        # Set health area from campaign if not provided
        if not self.health_area and self.campaign:
            self.health_area = self.campaign.health_area

        super().save(*args, **kwargs)

    def generate_patient_id(self):
        """
        Generate unique patient ID in format: TIKO-2025-0001
        """
        prefix = getattr(settings, 'PATIENT_ID_PREFIX', 'TIKO')
        year = getattr(settings, 'PATIENT_ID_YEAR', timezone.now().year)

        # Get the last patient ID for this year
        last_patient = Patient.objects.filter(
            patient_id__startswith=f"{prefix}-{year}-"
        ).order_by('patient_id').last()

        if last_patient:
            # Extract the number from the last patient ID
            try:
                last_number = int(last_patient.patient_id.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}-{year}-{new_number:04d}"

    def get_full_name(self):
        """Get patient's full name"""
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return " ".join(names)

    @property
    def age_display(self):
        """Get age with proper display"""
        if self.date_of_birth:
            today = timezone.now().date()
            calculated_age = today.year - self.date_of_birth.year
            if today.month < self.date_of_birth.month or \
               (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
                calculated_age -= 1
            return calculated_age
        return self.age

    def get_current_status_display(self):
        """Get current status with color coding"""
        status_colors = {
            'registered': 'secondary',
            'vitals_taken': 'info',
            'consultation_done': 'warning',
            'lab_ordered': 'primary',
            'lab_completed': 'success',
            'treatment_completed': 'success',
            'discharged': 'dark',
        }
        return {
            'status': self.get_status_display(),
            'color': status_colors.get(self.status, 'secondary')
        }


class ClinicalParameters(models.Model):
    """
    Model for storing patient vital signs and clinical parameters
    """
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name='clinical_parameters'
    )

    # Basic vitals
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Weight in kg"
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Height in cm"
    )
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        help_text="Temperature in Celsius"
    )

    # Blood pressure
    systolic_bp = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text="Systolic blood pressure (mmHg)"
    )
    diastolic_bp = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        help_text="Diastolic blood pressure (mmHg)"
    )

    # Heart rate
    heart_rate = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
        help_text="Heart rate (beats per minute)"
    )

    # Blood glucose
    GLUCOSE_TYPE_CHOICES = [
        ('fbs', 'Fasting Blood Sugar'),
        ('rbs', 'Random Blood Sugar'),
        ('pp', 'Post Prandial'),
    ]
    glucose_type = models.CharField(
        max_length=3,
        choices=GLUCOSE_TYPE_CHOICES,
        blank=True,
        null=True
    )
    blood_glucose = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Blood glucose level (mg/dL)"
    )

    # Women's health parameters
    lmp = models.DateField(
        blank=True,
        null=True,
        help_text="Last Menstrual Period"
    )

    # Teenage pregnancy fields
    is_pregnant = models.BooleanField(default=False)
    gestational_age = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        help_text="Gestational age in weeks"
    )
    age_at_first_pregnancy = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Age at first pregnancy"
    )

    # Additional notes
    notes = models.TextField(blank=True, null=True)

    # Tracking
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recorded_vitals'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clinical Parameters"
        verbose_name_plural = "Clinical Parameters"

    def __str__(self):
        return f"Vitals for {self.patient.patient_id}"

    @property
    def bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.weight and self.height:
            height_m = float(self.height) / 100  # Convert cm to meters
            return round(float(self.weight) / (height_m ** 2), 1)
        return None

    @property
    def bmi_category(self):
        """Get BMI category"""
        bmi = self.bmi
        if bmi is None:
            return None

        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal weight"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    @property
    def blood_pressure_display(self):
        """Get formatted blood pressure"""
        if self.systolic_bp and self.diastolic_bp:
            return f"{self.systolic_bp}/{self.diastolic_bp}"
        return None

    @property
    def blood_pressure_category(self):
        """Get blood pressure category"""
        if not (self.systolic_bp and self.diastolic_bp):
            return None

        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return "Normal"
        elif self.systolic_bp < 130 and self.diastolic_bp < 80:
            return "Elevated"
        elif self.systolic_bp < 140 or self.diastolic_bp < 90:
            return "High Blood Pressure Stage 1"
        elif self.systolic_bp < 180 or self.diastolic_bp < 120:
            return "High Blood Pressure Stage 2"
        else:
            return "Hypertensive Crisis"
