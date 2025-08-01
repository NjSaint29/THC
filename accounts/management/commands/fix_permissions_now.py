"""
Emergency command to immediately fix permission issues
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Command(BaseCommand):
    help = 'Immediately fix critical permission issues for patient registration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-admin-only',
            action='store_true',
            help='Only fix admin user permissions',
        )

    def handle(self, *args, **options):
        fix_admin_only = options['fix_admin_only']
        
        self.stdout.write('🚨 EMERGENCY PERMISSION FIX')
        self.stdout.write('=' * 40)
        
        try:
            # Step 1: Ensure critical permissions exist
            self.ensure_critical_permissions()
            
            # Step 2: Fix admin user immediately
            self.fix_admin_user()
            
            if not fix_admin_only:
                # Step 3: Set up all groups and permissions
                self.setup_all_groups_and_permissions()
                
                # Step 4: Fix all user assignments
                self.fix_all_user_assignments()
            
            self.stdout.write('\n✅ EMERGENCY FIX COMPLETED')
            self.stdout.write('🔗 Try accessing: https://thc-1.onrender.com/patients/register/')
            
        except Exception as e:
            self.stdout.write(f'\n❌ Error during fix: {str(e)}')
            self.stdout.write('🔧 Try manual fix in Django admin panel')

    def ensure_critical_permissions(self):
        self.stdout.write('\n🔐 Ensuring critical permissions exist...')
        
        # Get or create content types
        try:
            patient_ct = ContentType.objects.get(app_label='patients', model='patient')
            
            # Ensure can_register_patients permission exists
            perm, created = Permission.objects.get_or_create(
                codename='can_register_patients',
                content_type=patient_ct,
                defaults={'name': 'Can register patients'}
            )
            if created:
                self.stdout.write('  ✅ Created can_register_patients permission')
            else:
                self.stdout.write('  ✅ can_register_patients permission exists')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error with permissions: {str(e)}')

    def fix_admin_user(self):
        self.stdout.write('\n👑 Fixing admin user...')
        
        try:
            # Get or create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@tikohealthcampaign.com',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            
            if created:
                admin_user.set_password('TikoAdmin2025!')
                admin_user.save()
                self.stdout.write('  ✅ Created admin user')
            else:
                # Ensure admin has correct privileges
                if not admin_user.is_superuser or not admin_user.is_staff:
                    admin_user.is_superuser = True
                    admin_user.is_staff = True
                    admin_user.role = 'admin'
                    admin_user.save()
                    self.stdout.write('  ✅ Updated admin user privileges')
                else:
                    self.stdout.write('  ✅ Admin user exists with correct privileges')
            
            # Ensure admin is in Administrators group
            admin_group, created = Group.objects.get_or_create(name='Administrators')
            if not admin_user.groups.filter(name='Administrators').exists():
                admin_user.groups.add(admin_group)
                self.stdout.write('  ✅ Added admin to Administrators group')
            
            # Give Administrators group all permissions
            all_permissions = Permission.objects.all()
            admin_group.permissions.set(all_permissions)
            self.stdout.write(f'  ✅ Gave Administrators group all {all_permissions.count()} permissions')
            
            # Verify admin can register patients
            if admin_user.has_perm('patients.can_register_patients'):
                self.stdout.write('  ✅ Admin can register patients')
            else:
                self.stdout.write('  ⚠️  Admin still cannot register patients')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error fixing admin: {str(e)}')

    def setup_all_groups_and_permissions(self):
        self.stdout.write('\n👥 Setting up all groups and permissions...')

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
                'patients.view_patient',
                'consultations.view_consultation',
                'laboratory.view_labresult',
                'consultations.view_prescription',
            ],
            'Data Analysts': [
                'patients.view_patient',
                'patients.view_clinicalparameters',
                'consultations.view_consultation',
                'consultations.view_laborder',
                'laboratory.view_labresult',
                'consultations.view_prescription',
                'campaigns.view_campaign',
            ],
        }
        
        for group_name, permission_codes in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'  ✅ Created group: {group_name}')
            
            # Clear and add permissions
            group.permissions.clear()
            added_count = 0
            
            for perm_code in permission_codes:
                try:
                    app_label, codename = perm_code.split('.')
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    group.permissions.add(permission)
                    added_count += 1
                except Permission.DoesNotExist:
                    self.stdout.write(f'    ⚠️  Permission not found: {perm_code}')
            
            self.stdout.write(f'  ✅ {group_name}: {added_count} permissions assigned')

    def fix_all_user_assignments(self):
        self.stdout.write('\n🔗 Fixing user group assignments...')
        
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
        
        fixed_count = 0
        for user in User.objects.all():
            if user.role:
                group_name = role_group_mapping.get(user.role)
                if group_name:
                    try:
                        group = Group.objects.get(name=group_name)
                        if not user.groups.filter(name=group_name).exists():
                            user.groups.add(group)
                            fixed_count += 1
                            self.stdout.write(f'  ✅ Added {user.username} to {group_name}')
                    except Group.DoesNotExist:
                        self.stdout.write(f'  ❌ Group not found: {group_name}')
        
        self.stdout.write(f'  ✅ Fixed {fixed_count} user assignments')
