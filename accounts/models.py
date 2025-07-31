from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, UserManager
from django.contrib.contenttypes.models import ContentType


class UserRole:
    """
    Constants for user roles and their permissions
    """
    ADMIN = 'admin'
    CAMPAIGN_MANAGER = 'campaign_manager'
    REGISTRATION_CLERK = 'registration_clerk'
    VITALS_CLERK = 'vitals_clerk'
    DOCTOR = 'doctor'
    LAB_TECHNICIAN = 'lab_technician'
    PHARMACY_CLERK = 'pharmacy_clerk'
    DATA_ANALYST = 'data_analyst'

    choices = [
        (ADMIN, 'Administrator'),
        (CAMPAIGN_MANAGER, 'Campaign Manager'),
        (REGISTRATION_CLERK, 'Registration Clerk'),
        (VITALS_CLERK, 'Vitals Clerk'),
        (DOCTOR, 'Doctor'),
        (LAB_TECHNICIAN, 'Lab Technician'),
        (PHARMACY_CLERK, 'Pharmacy Clerk'),
        (DATA_ANALYST, 'Data Analyst'),
    ]


class CustomUserManager(UserManager):
    """
    Custom user manager that handles role assignment for superusers
    """
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # Set default role to admin if not provided
        if 'role' not in extra_fields:
            extra_fields['role'] = UserRole.ADMIN

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    role = models.CharField(
        max_length=50,
        choices=UserRole.choices,
        default=UserRole.REGISTRATION_CLERK,
        help_text="User's role in the health campaign"
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use custom manager
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return self.groups.filter(name=role_name).exists()

    def get_role_display(self):
        """Get the display name for the user's role"""
        return dict(UserRole.choices).get(self.role, self.role)

    def get_expected_group_name(self):
        """Get the expected group name for this user's role"""
        from accounts.signals import ROLE_GROUP_MAPPING
        return ROLE_GROUP_MAPPING.get(self.role)

    def is_in_correct_group(self):
        """Check if user is in the correct group for their role"""
        expected_group_name = self.get_expected_group_name()
        if not expected_group_name:
            return False
        return self.groups.filter(name=expected_group_name).exists()

    def fix_group_assignment(self):
        """Fix the user's group assignment based on their role"""
        from accounts.signals import ensure_user_has_correct_permissions
        return ensure_user_has_correct_permissions(self)


class AuditLog(models.Model):
    """
    Model to track all user actions for audit purposes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    changes = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.model_name} - {self.timestamp}"
