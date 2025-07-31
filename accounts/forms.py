from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from .models import User, UserRole


class CustomLoginForm(AuthenticationForm):
    """
    Custom login form with Bootstrap styling
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class PublicStaffRegistrationForm(UserCreationForm):
    """
    Public form for staff self-registration with the 4 main roles only
    """
    ROLE_CHOICES = [
        (UserRole.REGISTRATION_CLERK, 'Registration Clerk - Section A: Demographics'),
        (UserRole.VITALS_CLERK, 'Vitals Clerk - Section B: Clinical Parameters'),
        (UserRole.DOCTOR, 'Doctor - Sections C & E: Consultation & Prescriptions'),
        (UserRole.LAB_TECHNICIAN, 'Lab Technician - Section D: Laboratory Results'),
    ]

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'required': True
        })
    )

    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'required': True
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'required': True
        })
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text='Select your role and responsibilities in the health campaign'
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (optional)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone_number')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.is_active = True  # Auto-activate public registrations
        user.is_staff = True   # Allow access to system functions

        if commit:
            user.save()
            # Assign user to appropriate group based on role
            self.assign_user_to_group(user)

        return user

    def assign_user_to_group(self, user):
        """
        Assign user to the appropriate Django group based on their role
        """
        # Remove user from all existing groups
        user.groups.clear()

        # Map roles to group names
        role_group_mapping = {
            UserRole.REGISTRATION_CLERK: 'Registration Clerks',
            UserRole.VITALS_CLERK: 'Vitals Clerks',
            UserRole.DOCTOR: 'Doctors',
            UserRole.LAB_TECHNICIAN: 'Lab Technicians',
            UserRole.CAMPAIGN_MANAGER: 'Campaign Managers',
            UserRole.DATA_ANALYST: 'Data Analysts',
            UserRole.ADMIN: 'Administrators',
        }

        group_name = role_group_mapping.get(user.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                # Group doesn't exist yet, will be created by management command
                pass


class StaffRegistrationForm(UserCreationForm):
    """
    Form for registering new staff members with specific roles and permissions (Admin use)
    """
    ROLE_CHOICES = [
        (UserRole.REGISTRATION_CLERK, 'Registration Clerk'),
        (UserRole.VITALS_CLERK, 'Vitals Clerk'),
        (UserRole.DOCTOR, 'Doctor'),
        (UserRole.LAB_TECHNICIAN, 'Lab Technician'),
        (UserRole.CAMPAIGN_MANAGER, 'Campaign Manager'),
        (UserRole.DATA_ANALYST, 'Data Analyst'),
        (UserRole.ADMIN, 'Administrator'),
    ]
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'required': True
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'required': True
        })
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text='Select the staff member\'s role and responsibilities'
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (optional)'
        })
    )
    
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='User can log in and access the system'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.is_active = self.cleaned_data['is_active']
        
        if commit:
            user.save()
            # Assign user to appropriate group based on role
            self.assign_user_to_group(user)
        
        return user

    def assign_user_to_group(self, user):
        """
        Assign user to the appropriate Django group based on their role
        """
        # Remove user from all existing groups
        user.groups.clear()
        
        # Map roles to group names
        role_group_mapping = {
            UserRole.REGISTRATION_CLERK: 'Registration Clerks',
            UserRole.VITALS_CLERK: 'Vitals Clerks',
            UserRole.DOCTOR: 'Doctors',
            UserRole.LAB_TECHNICIAN: 'Lab Technicians',
            UserRole.CAMPAIGN_MANAGER: 'Campaign Managers',
            UserRole.DATA_ANALYST: 'Data Analysts',
            UserRole.ADMIN: 'Administrators',
        }
        
        group_name = role_group_mapping.get(user.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                # Group doesn't exist yet, will be created by management command
                pass


class StaffEditForm(forms.ModelForm):
    """
    Form for editing existing staff members
    """
    ROLE_CHOICES = [
        (UserRole.REGISTRATION_CLERK, 'Registration Clerk'),
        (UserRole.VITALS_CLERK, 'Vitals Clerk'),
        (UserRole.DOCTOR, 'Doctor'),
        (UserRole.LAB_TECHNICIAN, 'Lab Technician'),
        (UserRole.CAMPAIGN_MANAGER, 'Campaign Manager'),
        (UserRole.DATA_ANALYST, 'Data Analyst'),
        (UserRole.ADMIN, 'Administrator'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'phone_number', 'is_active')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=commit)
        
        if commit:
            # Update user group assignment
            self.assign_user_to_group(user)
        
        return user

    def assign_user_to_group(self, user):
        """
        Assign user to the appropriate Django group based on their role
        """
        # Remove user from all existing groups
        user.groups.clear()
        
        # Map roles to group names
        role_group_mapping = {
            UserRole.REGISTRATION_CLERK: 'Registration Clerks',
            UserRole.VITALS_CLERK: 'Vitals Clerks',
            UserRole.DOCTOR: 'Doctors',
            UserRole.LAB_TECHNICIAN: 'Lab Technicians',
            UserRole.CAMPAIGN_MANAGER: 'Campaign Managers',
            UserRole.DATA_ANALYST: 'Data Analysts',
            UserRole.ADMIN: 'Administrators',
        }
        
        group_name = role_group_mapping.get(user.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                # Group doesn't exist yet, will be created by management command
                pass


class RolePermissionForm(forms.Form):
    """
    Form to display role permissions (read-only)
    """
    ROLE_PERMISSIONS = {
        UserRole.REGISTRATION_CLERK: {
            'description': 'Handles section A: DEMOGRAPHIC AND BIOGRAPHIC DATA',
            'can_do': [
                'View list of active campaigns',
                'Register new patients',
                'Auto-generate Patient ID',
                'View patient demographics',
                'Edit patient demographics'
            ],
            'cannot_do': [
                'View or edit clinical parameters',
                'View or edit consultation/diagnosis',
                'View or edit lab results',
                'View or edit prescriptions'
            ]
        },
        UserRole.VITALS_CLERK: {
            'description': 'Handles section B: CLINICAL PARAMETERS',
            'can_do': [
                'Search by Patient ID or name',
                'View demographics (read-only)',
                'Enter/update clinical parameters',
                'Record weight, temperature, BP, HR, glucose',
                'Record height, LMP, pregnancy details'
            ],
            'cannot_do': [
                'Edit demographics',
                'View or edit consultation/diagnosis',
                'View or edit lab results',
                'View or edit prescriptions'
            ]
        },
        UserRole.DOCTOR: {
            'description': 'Handles sections C and E: MEDICAL CONSULTATION and PRESCRIPTIONS',
            'can_do': [
                'Search by Patient ID or name',
                'View full patient record (demographics + vitals + lab results)',
                'Enter/update consultation details',
                'Enter/update diagnosis',
                'Order lab tests',
                'Write prescriptions',
                'Make referrals'
            ],
            'cannot_do': [
                'Edit demographics',
                'Edit vitals',
                'Edit lab results'
            ]
        },
        UserRole.LAB_TECHNICIAN: {
            'description': 'Handles section D: LABORATORY TEST RESULTS',
            'can_do': [
                'Search by Patient ID or name',
                'View demographics, vitals, and requested tests',
                'Enter/update lab test results',
                'Add test conclusions',
                'Mark critical values'
            ],
            'cannot_do': [
                'Edit demographics',
                'Edit vitals',
                'Edit consultation/diagnosis',
                'Edit prescriptions'
            ]
        }
    }
    
    def __init__(self, role=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = role
        
    def get_role_info(self):
        return self.ROLE_PERMISSIONS.get(self.role, {})
