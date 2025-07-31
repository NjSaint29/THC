from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from patients.models import Patient
from campaigns.models import LabTest, Drug

User = get_user_model()


class Consultation(models.Model):
    """
    Model representing a medical consultation
    """
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='consultations'
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='consultations'
    )

    # Consultation details
    consultation_date = models.DateTimeField(default=timezone.now)

    # Chief complaint and history
    chief_complaint = models.TextField(
        blank=True, null=True,
        help_text="Patient's main complaint or reason for visit"
    )
    history_of_present_illness = models.TextField(
        blank=True, null=True,
        help_text="Detailed history of the current illness"
    )
    past_medical_history = models.TextField(
        blank=True, null=True,
        help_text="Previous medical conditions, surgeries, hospitalizations"
    )
    family_history = models.TextField(
        blank=True, null=True,
        help_text="Relevant family medical history"
    )
    social_history = models.TextField(
        blank=True, null=True,
        help_text="Lifestyle factors, occupation, habits"
    )

    # Physical examination
    general_appearance = models.TextField(
        blank=True, null=True,
        help_text="General appearance and mental state"
    )
    physical_examination = models.TextField(
        blank=True, null=True,
        help_text="Detailed physical examination findings"
    )

    # Assessment and plan
    clinical_assessment = models.TextField(
        blank=True, null=True,
        help_text="Clinical impression and assessment"
    )
    working_diagnosis = models.TextField(
        blank=True, null=True,
        help_text="Primary and differential diagnoses"
    )
    treatment_plan = models.TextField(
        blank=True, null=True,
        help_text="Treatment plan and recommendations"
    )

    # Follow-up and referrals
    follow_up_instructions = models.TextField(
        blank=True, null=True,
        help_text="Follow-up instructions for patient"
    )
    referral_needed = models.BooleanField(default=False)
    referral_to = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="Specialist or facility for referral"
    )
    referral_reason = models.TextField(
        blank=True, null=True,
        help_text="Reason for referral"
    )

    # Consultation status
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('follow_up_needed', 'Follow-up Needed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress'
    )

    # Additional notes
    additional_notes = models.TextField(
        blank=True, null=True,
        help_text="Any additional notes or observations"
    )

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-consultation_date']
        permissions = [
            ('can_conduct_consultations', 'Can conduct medical consultations'),
            ('can_view_consultation_reports', 'Can view consultation reports'),
        ]

    def __str__(self):
        return f"Consultation - {self.patient.patient_id} - {self.consultation_date.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update patient status
        if self.status == 'completed':
            self.patient.status = 'consultation_done'
            self.patient.save()


class LabOrder(models.Model):
    """
    Model for lab test orders during consultation
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='lab_orders'
    )

    # Lab test can be either from formulary or custom text
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Select from campaign formulary (optional)"
    )
    custom_test_name = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="Custom lab test name (if not in formulary)"
    )

    # Order details
    ordered_date = models.DateTimeField(default=timezone.now)
    urgency = models.CharField(
        max_length=20,
        choices=[
            ('routine', 'Routine'),
            ('urgent', 'Urgent'),
            ('stat', 'STAT'),
        ],
        default='routine'
    )
    clinical_indication = models.TextField(
        blank=True, null=True,
        help_text="Clinical reason for ordering this test"
    )

    # Simplified laboratory status
    LAB_STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    lab_status = models.CharField(
        max_length=20,
        choices=LAB_STATUS_CHOICES,
        default='ordered',
        help_text="Laboratory status: Ordered or Completed"
    )

    # Legacy status field for compatibility
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ordered'
    )

    # Additional notes
    notes = models.TextField(blank=True, null=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ordered_date']
        # Remove unique constraint since we now allow custom test names

    def get_test_name(self):
        """
        Return the test name - either from formulary or custom text
        """
        if self.custom_test_name:
            return self.custom_test_name
        elif self.lab_test:
            return self.lab_test.name
        else:
            return "Lab Test (To be specified)"

    def get_test_category(self):
        """
        Return the test category if available from formulary
        """
        if self.lab_test:
            return self.lab_test.category
        else:
            return "Custom Test"

    def get_specimen_type(self):
        """
        Return specimen type if available from formulary
        """
        if self.lab_test:
            return self.lab_test.specimen_type
        else:
            return None

    def is_ordered(self):
        """
        Check if test is ordered and awaiting results
        """
        return self.lab_status == 'ordered'

    def is_completed(self):
        """
        Check if test has been completed with results
        """
        return self.lab_status == 'completed'

    def can_enter_results(self):
        """
        Check if results can be entered (order is in ordered status)
        """
        return self.lab_status == 'ordered'

    def complete_with_results(self):
        """
        Mark lab order as completed when results are entered
        """
        self.lab_status = 'completed'
        self.status = 'completed'  # Update legacy status field
        self.save()

    def __str__(self):
        return f"{self.get_test_name()} - {self.consultation.patient.patient_id}"

    def clean(self):
        """
        No validation - allow flexible lab order creation
        """
        pass


class Prescription(models.Model):
    """
    Model for prescriptions during consultation
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )

    # Drug can be either from formulary or custom text
    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Select from campaign formulary (optional)"
    )
    custom_drug_name = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="Custom drug name (if not in formulary)"
    )

    # Prescription details (can be completed by pharmacy)
    dosage = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="e.g., 500mg, 1 tablet, 5ml (can be completed by pharmacy)"
    )
    frequency = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="e.g., twice daily, every 8 hours, as needed (can be completed by pharmacy)"
    )
    duration = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="e.g., 7 days, 2 weeks, until finished (can be completed by pharmacy)"
    )
    route = models.CharField(
        max_length=50,
        choices=[
            ('oral', 'Oral'),
            ('topical', 'Topical'),
            ('injection', 'Injection'),
            ('inhalation', 'Inhalation'),
            ('other', 'Other'),
        ],
        default='oral'
    )

    # Instructions
    instructions = models.TextField(
        blank=True, null=True,
        help_text="Special instructions for taking the medication"
    )
    indication = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="What the medication is for"
    )

    # Quantity and refills
    quantity = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Total quantity to dispense"
    )
    refills = models.PositiveIntegerField(
        default=0,
        help_text="Number of refills allowed"
    )

    # Pharmacy workflow status
    PHARMACY_STATUS_CHOICES = [
        ('pending_review', 'Pending Pharmacy Review'),
        ('details_needed', 'Dosage Details Needed'),
        ('ready_to_dispense', 'Ready to Dispense'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled'),
    ]
    pharmacy_status = models.CharField(
        max_length=20,
        choices=PHARMACY_STATUS_CHOICES,
        default='pending_review',
        help_text="Pharmacy workflow status"
    )

    # Dispensing status (legacy field for compatibility)
    STATUS_CHOICES = [
        ('prescribed', 'Prescribed'),
        ('dispensed', 'Dispensed'),
        ('partially_dispensed', 'Partially Dispensed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='prescribed'
    )

    # Dispensing details
    dispensed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dispensed_prescriptions'
    )
    dispensed_date = models.DateTimeField(blank=True, null=True)
    dispensed_quantity = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Actual quantity dispensed"
    )

    # Additional notes
    notes = models.TextField(blank=True, null=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_drug_name(self):
        """
        Return the drug name - either from formulary or custom text
        """
        if self.custom_drug_name:
            return self.custom_drug_name
        elif self.drug:
            return self.drug.name
        else:
            return "Medication (To be specified)"

    def get_drug_category(self):
        """
        Return the drug category if available from formulary
        """
        if self.drug:
            return self.drug.category
        else:
            return "Custom Medication"

    def get_drug_strength(self):
        """
        Return drug strength if available from formulary
        """
        if self.drug:
            return self.drug.strength
        else:
            return None

    def needs_pharmacy_review(self):
        """
        Check if prescription needs pharmacy review for dosage details
        """
        return not all([self.dosage, self.frequency, self.duration])

    def is_ready_to_dispense(self):
        """
        Check if prescription has all required details for dispensing
        """
        return all([self.dosage, self.frequency, self.duration]) and self.pharmacy_status == 'ready_to_dispense'

    def update_pharmacy_status(self):
        """
        Automatically update pharmacy status based on prescription completeness
        """
        if self.needs_pharmacy_review():
            self.pharmacy_status = 'details_needed'
        elif all([self.dosage, self.frequency, self.duration]):
            if self.pharmacy_status in ['pending_review', 'details_needed']:
                self.pharmacy_status = 'ready_to_dispense'

    def __str__(self):
        return f"{self.get_drug_name()} - {self.consultation.patient.patient_id}"

    def clean(self):
        """
        No validation - allow flexible prescription creation
        """
        pass

    @property
    def prescription_summary(self):
        """Get a summary of the prescription"""
        parts = [self.get_drug_name()]
        if self.dosage:
            parts.append(self.dosage)
        if self.frequency:
            parts.append(self.frequency)
        if self.duration:
            parts.append(f"for {self.duration}")
        return " ".join(parts)
