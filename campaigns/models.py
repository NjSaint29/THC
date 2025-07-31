from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class Campaign(models.Model):
    """
    Model representing a health campaign
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    health_area = models.CharField(max_length=200)
    consent_text = models.TextField(
        help_text="Consent text that patients will agree to during registration"
    )

    # Campaign status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Campaign management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campaign settings
    max_patients = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Maximum number of patients for this campaign (optional)"
    )

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_manage_campaigns', 'Can manage campaigns'),
            ('can_view_campaign_reports', 'Can view campaign reports'),
        ]

    def __str__(self):
        return f"{self.name} ({self.health_area})"

    @property
    def is_active(self):
        """Check if campaign is currently active"""
        today = timezone.now().date()
        return (
            self.status == 'active' and
            self.start_date <= today <= self.end_date
        )

    @property
    def patient_count(self):
        """Get total number of registered patients"""
        return self.patients.count()

    @property
    def days_remaining(self):
        """Get number of days remaining in campaign"""
        if self.status != 'active':
            return 0
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days


class LabTest(models.Model):
    """
    Model for lab tests available in campaigns
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    normal_range = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)

    # Test categorization
    CATEGORY_CHOICES = [
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('stool', 'Stool Test'),
        ('imaging', 'Imaging'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='blood')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Drug(models.Model):
    """
    Model for drugs available in campaigns (formulary)
    """
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True, null=True)
    strength = models.CharField(max_length=50, blank=True, null=True)
    dosage_form = models.CharField(max_length=50, blank=True, null=True)

    # Drug categorization
    CATEGORY_CHOICES = [
        ('analgesic', 'Analgesic'),
        ('antibiotic', 'Antibiotic'),
        ('antihypertensive', 'Antihypertensive'),
        ('antidiabetic', 'Antidiabetic'),
        ('vitamin', 'Vitamin/Supplement'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = ['name', 'strength', 'dosage_form']

    def __str__(self):
        parts = [self.name]
        if self.strength:
            parts.append(self.strength)
        if self.dosage_form:
            parts.append(f"({self.dosage_form})")
        return " ".join(parts)


class CampaignLabTest(models.Model):
    """
    Many-to-many relationship between campaigns and lab tests
    """
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='lab_tests')
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    is_default = models.BooleanField(
        default=False,
        help_text="If true, this test will be automatically selected for new patients"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['campaign', 'lab_test']
        ordering = ['order', 'lab_test__name']

    def __str__(self):
        return f"{self.campaign.name} - {self.lab_test.name}"


class CampaignDrug(models.Model):
    """
    Many-to-many relationship between campaigns and drugs (formulary)
    """
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='formulary')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    is_preferred = models.BooleanField(
        default=False,
        help_text="If true, this drug will be highlighted as preferred"
    )
    stock_quantity = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Available stock for this campaign (optional)"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['campaign', 'drug']
        ordering = ['order', 'drug__name']

    def __str__(self):
        return f"{self.campaign.name} - {self.drug.name}"
