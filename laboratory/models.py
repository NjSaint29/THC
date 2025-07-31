from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from consultations.models import LabOrder
from campaigns.models import LabTest

User = get_user_model()


class LabResult(models.Model):
    """
    Model for storing laboratory test results
    """
    lab_order = models.OneToOneField(
        LabOrder,
        on_delete=models.CASCADE,
        related_name='result'
    )

    # Result details
    result_value = models.TextField(
        help_text="The actual test result value"
    )
    result_unit = models.CharField(
        max_length=50,
        blank=True, null=True,
        help_text="Unit of measurement for the result"
    )
    reference_range = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="Normal reference range for this test"
    )

    # Result interpretation
    INTERPRETATION_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal_low', 'Abnormal - Low'),
        ('abnormal_high', 'Abnormal - High'),
        ('critical_low', 'Critical - Low'),
        ('critical_high', 'Critical - High'),
        ('inconclusive', 'Inconclusive'),
    ]
    interpretation = models.CharField(
        max_length=20,
        choices=INTERPRETATION_CHOICES,
        blank=True, null=True
    )

    # Lab technician notes and conclusion
    technician_notes = models.TextField(
        blank=True, null=True,
        help_text="Technical notes about the test procedure or sample"
    )
    clinical_conclusion = models.TextField(
        blank=True, null=True,
        help_text="Clinical interpretation and conclusion"
    )

    # Quality control
    sample_quality = models.CharField(
        max_length=20,
        choices=[
            ('good', 'Good'),
            ('acceptable', 'Acceptable'),
            ('poor', 'Poor - Repeat Required'),
            ('hemolyzed', 'Hemolyzed'),
            ('clotted', 'Clotted'),
            ('insufficient', 'Insufficient Sample'),
        ],
        default='good'
    )

    # Test methodology and equipment
    test_method = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="Method or equipment used for testing"
    )

    # Critical values notification
    is_critical = models.BooleanField(
        default=False,
        help_text="Mark if result requires immediate attention"
    )
    critical_notified = models.BooleanField(
        default=False,
        help_text="Mark if critical result has been communicated"
    )
    critical_notified_at = models.DateTimeField(
        blank=True, null=True,
        help_text="When critical result was communicated"
    )

    # Result status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('reported', 'Reported'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Tracking information
    technician = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lab_results'
    )
    result_date = models.DateTimeField(default=timezone.now)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_lab_results',
        help_text="Lab supervisor who verified the result"
    )
    verified_at = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-result_date']
        permissions = [
            ('can_enter_lab_results', 'Can enter laboratory results'),
            ('can_verify_lab_results', 'Can verify laboratory results'),
            ('can_view_lab_reports', 'Can view laboratory reports'),
        ]

    def __str__(self):
        test_name = self.lab_order.get_test_name()
        patient_id = self.lab_order.consultation.patient.patient_id
        return f"{test_name} - {patient_id}"

    def save(self, *args, **kwargs):
        # Auto-set reference range from lab test if not provided
        if (not self.reference_range and self.lab_order.lab_test and
            hasattr(self.lab_order.lab_test, 'normal_range') and
            self.lab_order.lab_test.normal_range):
            self.reference_range = self.lab_order.lab_test.normal_range

        # Auto-set unit from lab test if not provided
        if (not self.result_unit and self.lab_order.lab_test and
            hasattr(self.lab_order.lab_test, 'unit') and
            self.lab_order.lab_test.unit):
            self.result_unit = self.lab_order.lab_test.unit

        super().save(*args, **kwargs)

        # Update lab order status
        if self.status == 'completed':
            self.lab_order.status = 'completed'
            self.lab_order.save()

    @property
    def patient(self):
        """Get the patient for this lab result"""
        return self.lab_order.consultation.patient

    @property
    def doctor(self):
        """Get the doctor who ordered this test"""
        return self.lab_order.consultation.doctor

    @property
    def is_abnormal(self):
        """Check if result is abnormal"""
        return self.interpretation in ['abnormal_low', 'abnormal_high', 'critical_low', 'critical_high']

    @property
    def needs_attention(self):
        """Check if result needs immediate attention"""
        return self.is_critical or self.interpretation in ['critical_low', 'critical_high']

    def get_interpretation_color(self):
        """Get color class for result interpretation"""
        color_map = {
            'normal': 'success',
            'abnormal_low': 'warning',
            'abnormal_high': 'warning',
            'critical_low': 'danger',
            'critical_high': 'danger',
            'inconclusive': 'secondary',
        }
        return color_map.get(self.interpretation, 'secondary')


class LabWorksheet(models.Model):
    """
    Model for organizing lab work by batches/worksheets
    """
    worksheet_number = models.CharField(max_length=50, unique=True)
    test_type = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    technician = models.ForeignKey(User, on_delete=models.CASCADE)

    # Worksheet details
    created_date = models.DateField(default=timezone.now)
    run_date = models.DateTimeField(blank=True, null=True)

    STATUS_CHOICES = [
        ('created', 'Created'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    # Quality control
    control_results = models.TextField(
        blank=True, null=True,
        help_text="Quality control results for this batch"
    )

    notes = models.TextField(blank=True, null=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date', '-created_at']

    def __str__(self):
        return f"Worksheet {self.worksheet_number} - {self.test_type.name}"

    @property
    def sample_count(self):
        """Get number of samples in this worksheet"""
        return self.lab_orders.count()

    def generate_worksheet_number(self):
        """Generate unique worksheet number"""
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')

        # Get last worksheet for today
        last_worksheet = LabWorksheet.objects.filter(
            created_date=today
        ).order_by('worksheet_number').last()

        if last_worksheet:
            try:
                last_number = int(last_worksheet.worksheet_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"WS-{date_str}-{new_number:03d}"


class LabOrderWorksheet(models.Model):
    """
    Many-to-many relationship between lab orders and worksheets
    """
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='worksheets')
    worksheet = models.ForeignKey(LabWorksheet, on_delete=models.CASCADE, related_name='lab_orders')
    position = models.PositiveIntegerField(
        help_text="Position of sample in the worksheet"
    )

    class Meta:
        unique_together = ['lab_order', 'worksheet']
        ordering = ['position']

    def __str__(self):
        return f"{self.worksheet.worksheet_number} - Position {self.position}"
