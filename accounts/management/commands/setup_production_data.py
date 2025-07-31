"""
Management command to set up production data and permissions
"""
import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.core import serializers
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up production data and permissions from SQLite export'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='data_export',
            help='Directory containing exported data files',
        )
        parser.add_argument(
            '--skip-import',
            action='store_true',
            help='Skip data import, only set up permissions',
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        skip_import = options['skip_import']
        
        self.stdout.write('Setting up production data and permissions...')
        
        # Step 1: Set up groups and permissions
        self.setup_groups_and_permissions()
        
        # Step 2: Import data if requested
        if not skip_import:
            self.import_data(data_dir)
        
        # Step 3: Fix user roles and permissions
        self.fix_user_permissions()
        
        # Step 4: Create admin user if needed
        self.ensure_admin_user()
        
        self.stdout.write(
            self.style.SUCCESS('Production setup completed successfully!')
        )

    def setup_groups_and_permissions(self):
        """Set up all groups and their permissions"""
        self.stdout.write('Setting up groups and permissions...')
        
        # Define groups and their permissions
        groups_permissions = {
            'Registration Clerks': [
                'patients.add_patient',
                'patients.change_patient', 
                'patients.view_patient',
                'patients.can_register_patients',
                'consultations.view_consultation',
            ],
            
            'Vitals Clerks': [
                'patients.view_patient',
                'patients.change_patient',
                'patients.add_clinicalparameters',
                'patients.change_clinicalparameters',
                'patients.view_clinicalparameters',
                'consultations.view_consultation',
                'consultations.change_consultation',
            ],
            
            'Doctors': [
                'patients.view_patient',
                'patients.change_patient',
                'patients.view_clinicalparameters',
                'consultations.add_consultation',
                'consultations.change_consultation',
                'consultations.view_consultation',
                'consultations.delete_consultation',
                'consultations.can_conduct_consultations',
                'consultations.can_view_consultation_reports',
                'consultations.add_laborder',
                'consultations.change_laborder',
                'consultations.view_laborder',
                'consultations.delete_laborder',
                'laboratory.view_labresult',
                'laboratory.can_view_lab_reports',
                'consultations.add_prescription',
                'consultations.change_prescription',
                'consultations.view_prescription',
                'consultations.delete_prescription',
            ],
            
            'Lab Technicians': [
                'patients.view_patient',
                'patients.view_clinicalparameters',
                'consultations.view_laborder',
                'consultations.change_laborder',
                'laboratory.add_labresult',
                'laboratory.change_labresult',
                'laboratory.view_labresult',
                'laboratory.delete_labresult',
                'laboratory.can_enter_lab_results',
                'laboratory.can_verify_lab_results',
                'laboratory.can_view_lab_reports',
                'consultations.view_consultation',
            ],
            
            'Pharmacy Clerks': [
                'patients.view_patient',
                'consultations.view_consultation',
                'consultations.change_consultation',
                'consultations.view_prescription',
                'consultations.change_prescription',
                'consultations.can_dispense_medications',
            ],
            
            'Campaign Managers': [
                'campaigns.add_campaign',
                'campaigns.change_campaign',
                'campaigns.view_campaign',
                'campaigns.delete_campaign',
                'campaigns.can_manage_campaigns',
                'campaigns.can_view_campaign_reports',
                'patients.view_patient',
                'patients.view_clinicalparameters',
                'consultations.view_consultation',
                'consultations.can_view_consultation_reports',
                'consultations.view_laborder',
                'laboratory.view_labresult',
                'laboratory.can_view_lab_reports',
                'consultations.view_prescription',
            ],
            
            'Data Analysts': [
                'patients.view_patient',
                'patients.can_view_patient_reports',
                'patients.view_clinicalparameters',
                'consultations.view_consultation',
                'consultations.can_view_consultation_reports',
                'consultations.view_laborder',
                'laboratory.view_labresult',
                'laboratory.can_view_lab_reports',
                'consultations.view_prescription',
                'campaigns.view_campaign',
                'campaigns.can_view_campaign_reports',
            ],
            
            'Administrators': [
                # All permissions - will be added dynamically
            ],
        }
        
        # Create groups and assign permissions
        for group_name, permission_codenames in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')
            
            # For administrators, give all permissions
            if group_name == 'Administrators':
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(f'Added all {all_permissions.count()} permissions to Administrators')
            else:
                # Clear existing permissions
                group.permissions.clear()
                
                # Add permissions to group
                added_count = 0
                for codename in permission_codenames:
                    try:
                        permission = Permission.objects.get(codename=codename.split('.')[-1])
                        group.permissions.add(permission)
                        added_count += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(f'Warning: Permission {codename} not found')
                
                self.stdout.write(f'Added {added_count} permissions to {group_name}')
            
            group.save()

    def import_data(self, data_dir):
        """Import data from export files"""
        if not os.path.exists(data_dir):
            self.stdout.write(f'Data directory not found: {data_dir}')
            return
        
        self.stdout.write(f'Importing data from: {data_dir}')
        
        # Import order matters due to foreign key dependencies
        import_files = [
            ('users.json', 'Users'),
            ('campaigns.json', 'Campaigns'),
            ('lab_tests.json', 'Lab Tests'),
            ('patients.json', 'Patients'),
            ('clinical_parameters.json', 'Clinical Parameters'),
            ('consultations.json', 'Consultations'),
            ('lab_orders.json', 'Lab Orders'),
            ('lab_results.json', 'Lab Results'),
        ]
        
        for filename, description in import_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = f.read()
                    
                    objects = serializers.deserialize('json', data)
                    count = 0
                    for obj in objects:
                        try:
                            obj.save()
                            count += 1
                        except Exception as e:
                            self.stdout.write(f'Error saving {description} object: {str(e)}')
                    
                    self.stdout.write(f'Imported {count} {description}')
                    
                except Exception as e:
                    self.stdout.write(f'Error importing {description}: {str(e)}')

    def fix_user_permissions(self):
        """Fix user roles and group assignments"""
        self.stdout.write('Fixing user permissions...')
        
        role_group_mapping = {
            'registration_clerk': 'Registration Clerks',
            'vitals_clerk': 'Vitals Clerks',
            'doctor': 'Doctors',
            'lab_technician': 'Lab Technicians',
            'pharmacy_clerk': 'Pharmacy Clerks',
            'campaign_manager': 'Campaign Managers',
            'data_analyst': 'Data Analysts',
            'admin': 'Administrators',
        }
        
        users_fixed = 0
        for user in User.objects.all():
            if user.role:
                group_name = role_group_mapping.get(user.role)
                if group_name:
                    try:
                        group = Group.objects.get(name=group_name)
                        if not user.groups.filter(name=group_name).exists():
                            user.groups.add(group)
                            users_fixed += 1
                        
                        # Set admin privileges for admin users
                        if user.role == 'admin':
                            if not user.is_staff or not user.is_superuser:
                                user.is_staff = True
                                user.is_superuser = True
                                user.save()
                                
                    except Group.DoesNotExist:
                        self.stdout.write(f'Group {group_name} not found for user {user.username}')
        
        self.stdout.write(f'Fixed permissions for {users_fixed} users')

    def ensure_admin_user(self):
        """Ensure there's at least one admin user"""
        admin_users = User.objects.filter(role='admin')
        if not admin_users.exists():
            self.stdout.write('Creating default admin user...')
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@tikohealthcampaign.com',
                password='TikoAdmin2025!',
                first_name='System',
                last_name='Administrator',
                role='admin',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            # Add to Administrators group
            admin_group = Group.objects.get(name='Administrators')
            admin_user.groups.add(admin_group)
            
            self.stdout.write('Default admin user created successfully')
        else:
            self.stdout.write(f'Found {admin_users.count()} admin users')
