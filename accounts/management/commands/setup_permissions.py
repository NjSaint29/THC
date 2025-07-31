from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from patients.models import Patient, ClinicalParameters
from consultations.models import Consultation, LabOrder, Prescription
from laboratory.models import LabResult
from campaigns.models import Campaign


class Command(BaseCommand):
    help = 'Set up user groups and permissions for Tiko Health Campaign'

    def handle(self, *args, **options):
        self.stdout.write('Setting up user groups and permissions...')
        
        # Create Groups
        registration_group, _ = Group.objects.get_or_create(name='Registration Clerks')
        vitals_group, _ = Group.objects.get_or_create(name='Vitals Clerks')
        doctors_group, _ = Group.objects.get_or_create(name='Doctors')
        lab_group, _ = Group.objects.get_or_create(name='Lab Technicians')
        pharmacy_group, _ = Group.objects.get_or_create(name='Pharmacy Clerks')
        campaign_group, _ = Group.objects.get_or_create(name='Campaign Managers')
        analyst_group, _ = Group.objects.get_or_create(name='Data Analysts')
        admin_group, _ = Group.objects.get_or_create(name='Administrators')
        
        # Get content types
        patient_ct = ContentType.objects.get_for_model(Patient)
        vitals_ct = ContentType.objects.get_for_model(ClinicalParameters)
        consultation_ct = ContentType.objects.get_for_model(Consultation)
        laborder_ct = ContentType.objects.get_for_model(LabOrder)
        prescription_ct = ContentType.objects.get_for_model(Prescription)
        labresult_ct = ContentType.objects.get_for_model(LabResult)
        campaign_ct = ContentType.objects.get_for_model(Campaign)
        
        # Registration Clerk Permissions
        registration_permissions = [
            # Can view active campaigns
            Permission.objects.get_or_create(
                codename='view_active_campaigns',
                name='Can view active campaigns',
                content_type=campaign_ct
            )[0],
            # Can register new patients (custom permission)
            Permission.objects.get_or_create(
                codename='can_register_patients',
                name='Can register patients',
                content_type=patient_ct
            )[0],
            # Standard patient permissions
            Permission.objects.get(codename='add_patient', content_type=patient_ct),
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            Permission.objects.get(codename='change_patient', content_type=patient_ct),
        ]
        
        # Vitals Clerk Permissions
        vitals_permissions = [
            # Can view patient demographics (read-only)
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            # Can add/update clinical parameters
            Permission.objects.get(codename='add_clinicalparameters', content_type=vitals_ct),
            Permission.objects.get(codename='change_clinicalparameters', content_type=vitals_ct),
            Permission.objects.get(codename='view_clinicalparameters', content_type=vitals_ct),
        ]
        
        # Doctor Permissions
        doctor_permissions = [
            # Can view full patient record
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            Permission.objects.get(codename='view_clinicalparameters', content_type=vitals_ct),
            Permission.objects.get(codename='view_labresult', content_type=labresult_ct),
            # Can manage consultations (including custom permission)
            Permission.objects.get_or_create(
                codename='can_conduct_consultations',
                name='Can conduct medical consultations',
                content_type=consultation_ct
            )[0],
            Permission.objects.get(codename='add_consultation', content_type=consultation_ct),
            Permission.objects.get(codename='change_consultation', content_type=consultation_ct),
            Permission.objects.get(codename='view_consultation', content_type=consultation_ct),
            # Can order lab tests
            Permission.objects.get(codename='add_laborder', content_type=laborder_ct),
            Permission.objects.get(codename='change_laborder', content_type=laborder_ct),
            Permission.objects.get(codename='view_laborder', content_type=laborder_ct),
            # Can write prescriptions
            Permission.objects.get(codename='add_prescription', content_type=prescription_ct),
            Permission.objects.get(codename='change_prescription', content_type=prescription_ct),
            Permission.objects.get(codename='view_prescription', content_type=prescription_ct),
        ]
        
        # Lab Technician Permissions
        lab_permissions = [
            # Can view demographics and vitals (read-only)
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            Permission.objects.get(codename='view_clinicalparameters', content_type=vitals_ct),
            # Can view lab orders
            Permission.objects.get(codename='view_laborder', content_type=laborder_ct),
            # Can enter/update lab results (including custom permission)
            Permission.objects.get_or_create(
                codename='can_enter_lab_results',
                name='Can enter laboratory results',
                content_type=labresult_ct
            )[0],
            Permission.objects.get(codename='add_labresult', content_type=labresult_ct),
            Permission.objects.get(codename='change_labresult', content_type=labresult_ct),
            Permission.objects.get(codename='view_labresult', content_type=labresult_ct),
        ]

        # Campaign Manager Permissions
        campaign_permissions = [
            # Can manage campaigns
            Permission.objects.get(codename='add_campaign', content_type=campaign_ct),
            Permission.objects.get(codename='change_campaign', content_type=campaign_ct),
            Permission.objects.get(codename='view_campaign', content_type=campaign_ct),
            # Can view all patient data (read-only)
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            Permission.objects.get(codename='view_clinicalparameters', content_type=vitals_ct),
            Permission.objects.get(codename='view_consultation', content_type=consultation_ct),
            Permission.objects.get(codename='view_labresult', content_type=labresult_ct),
            Permission.objects.get(codename='view_prescription', content_type=prescription_ct),
        ]

        # Pharmacy Clerk Permissions
        pharmacy_permissions = [
            # Can view patients and prescriptions for dispensing
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            Permission.objects.get(codename='view_consultation', content_type=consultation_ct),
            Permission.objects.get(codename='view_prescription', content_type=prescription_ct),
            # Custom permissions for pharmacy operations
            Permission.objects.get_or_create(
                codename='can_dispense_medications',
                name='Can dispense medications',
                content_type=prescription_ct
            )[0],
        ]

        # Data Analyst Permissions
        analyst_permissions = [
            # Can view all data for analysis (read-only)
            Permission.objects.get(codename='view_campaign', content_type=campaign_ct),
            Permission.objects.get(codename='view_patient', content_type=patient_ct),
            Permission.objects.get(codename='view_clinicalparameters', content_type=vitals_ct),
            Permission.objects.get(codename='view_consultation', content_type=consultation_ct),
            Permission.objects.get(codename='view_labresult', content_type=labresult_ct),
            Permission.objects.get(codename='view_prescription', content_type=prescription_ct),
            # Custom permissions for reports
            Permission.objects.get_or_create(
                codename='can_view_patient_reports',
                name='Can view patient reports',
                content_type=patient_ct
            )[0],
        ]

        # Administrator Permissions (all permissions)
        admin_permissions = list(set(
            registration_permissions +
            vitals_permissions +
            doctor_permissions +
            lab_permissions +
            pharmacy_permissions +
            campaign_permissions +
            analyst_permissions
        ))

        # Add additional admin-only permissions
        user_ct = ContentType.objects.get_for_model(User)
        admin_permissions.extend([
            Permission.objects.get(codename='add_user', content_type=user_ct),
            Permission.objects.get(codename='change_user', content_type=user_ct),
            Permission.objects.get(codename='delete_user', content_type=user_ct),
            Permission.objects.get(codename='view_user', content_type=user_ct),
        ])

        # Assign permissions to groups
        registration_group.permissions.set(registration_permissions)
        vitals_group.permissions.set(vitals_permissions)
        doctors_group.permissions.set(doctor_permissions)
        lab_group.permissions.set(lab_permissions)
        pharmacy_group.permissions.set(pharmacy_permissions)
        campaign_group.permissions.set(campaign_permissions)
        analyst_group.permissions.set(analyst_permissions)
        admin_group.permissions.set(admin_permissions)

        self.stdout.write(
            self.style.SUCCESS('Successfully set up user groups and permissions!')
        )

        # Display summary
        self.stdout.write('\nGroups created:')
        self.stdout.write(f'- Registration Clerks: {len(registration_permissions)} permissions')
        self.stdout.write(f'- Vitals Clerks: {len(vitals_permissions)} permissions')
        self.stdout.write(f'- Doctors: {len(doctor_permissions)} permissions')
        self.stdout.write(f'- Lab Technicians: {len(lab_permissions)} permissions')
        self.stdout.write(f'- Pharmacy Clerks: {len(pharmacy_permissions)} permissions')
        self.stdout.write(f'- Campaign Managers: {len(campaign_permissions)} permissions')
        self.stdout.write(f'- Data Analysts: {len(analyst_permissions)} permissions')
        self.stdout.write(f'- Administrators: {len(admin_permissions)} permissions')
