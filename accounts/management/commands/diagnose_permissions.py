"""
Management command to diagnose permission issues in production
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnose permission and group setup issues'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DIAGNOSING TIKO HEALTH CAMPAIGN PERMISSIONS')
        self.stdout.write('=' * 60)
        
        # Check 1: User count and admin users
        self.check_users()
        
        # Check 2: Groups existence
        self.check_groups()
        
        # Check 3: Critical permissions
        self.check_permissions()
        
        # Check 4: User-group assignments
        self.check_user_groups()
        
        # Check 5: Admin user permissions
        self.check_admin_permissions()
        
        # Provide recommendations
        self.provide_recommendations()

    def check_users(self):
        self.stdout.write('\n📊 USER ANALYSIS:')
        total_users = User.objects.count()
        admin_users = User.objects.filter(is_superuser=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        
        self.stdout.write(f'  Total users: {total_users}')
        self.stdout.write(f'  Admin users (superuser): {admin_users}')
        self.stdout.write(f'  Staff users: {staff_users}')
        
        # List all users with their roles
        if total_users <= 20:  # Only show if reasonable number
            self.stdout.write('\n  User Details:')
            for user in User.objects.all():
                groups = ', '.join([g.name for g in user.groups.all()]) or 'No groups'
                self.stdout.write(f'    - {user.username}: role={user.role or "None"}, groups=[{groups}], superuser={user.is_superuser}')

    def check_groups(self):
        self.stdout.write('\n👥 GROUP ANALYSIS:')
        expected_groups = [
            'Registration Clerks',
            'Vitals Clerks',
            'Doctors',
            'Lab Technicians',
            'Pharmacy Clerks',
            'Campaign Managers',
            'Data Analysts',
            'Administrators',
        ]
        
        existing_groups = Group.objects.all()
        self.stdout.write(f'  Total groups: {existing_groups.count()}')
        
        for group_name in expected_groups:
            try:
                group = Group.objects.get(name=group_name)
                permission_count = group.permissions.count()
                user_count = group.user_set.count()
                status = '✅' if permission_count > 0 else '⚠️'
                self.stdout.write(f'  {status} {group_name}: {permission_count} permissions, {user_count} users')
            except Group.DoesNotExist:
                self.stdout.write(f'  ❌ {group_name}: NOT FOUND')

    def check_permissions(self):
        self.stdout.write('\n🔐 CRITICAL PERMISSIONS CHECK:')
        critical_permissions = [
            'patients.can_register_patients',
            'patients.add_patient',
            'patients.view_patient',
            'consultations.can_conduct_consultations',
            'laboratory.can_enter_lab_results',
        ]
        
        for perm_code in critical_permissions:
            app_label, codename = perm_code.split('.')
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                groups_with_perm = Group.objects.filter(permissions=permission)
                group_names = ', '.join([g.name for g in groups_with_perm])
                self.stdout.write(f'  ✅ {perm_code}: Found, assigned to [{group_names}]')
            except Permission.DoesNotExist:
                self.stdout.write(f'  ❌ {perm_code}: NOT FOUND')

    def check_user_groups(self):
        self.stdout.write('\n🔗 USER-GROUP ASSIGNMENTS:')
        
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
        
        users_with_issues = 0
        for user in User.objects.all():
            if user.role:
                expected_group = role_group_mapping.get(user.role)
                if expected_group:
                    try:
                        group = Group.objects.get(name=expected_group)
                        if user.groups.filter(name=expected_group).exists():
                            status = '✅'
                        else:
                            status = '❌'
                            users_with_issues += 1
                        self.stdout.write(f'  {status} {user.username} (role: {user.role}) -> {expected_group}')
                    except Group.DoesNotExist:
                        self.stdout.write(f'  ❌ {user.username} (role: {user.role}) -> {expected_group} (GROUP NOT FOUND)')
                        users_with_issues += 1
        
        self.stdout.write(f'\n  Users with assignment issues: {users_with_issues}')

    def check_admin_permissions(self):
        self.stdout.write('\n👑 ADMIN USER PERMISSIONS:')
        
        try:
            admin_user = User.objects.filter(username='admin').first()
            if admin_user:
                has_register_perm = admin_user.has_perm('patients.can_register_patients')
                has_add_patient = admin_user.has_perm('patients.add_patient')
                is_in_admin_group = admin_user.groups.filter(name='Administrators').exists()
                
                self.stdout.write(f'  Admin user found: {admin_user.username}')
                self.stdout.write(f'  ✅ Is superuser: {admin_user.is_superuser}')
                self.stdout.write(f'  {"✅" if has_register_perm else "❌"} Has can_register_patients: {has_register_perm}')
                self.stdout.write(f'  {"✅" if has_add_patient else "❌"} Has add_patient: {has_add_patient}')
                self.stdout.write(f'  {"✅" if is_in_admin_group else "❌"} In Administrators group: {is_in_admin_group}')
                
                # Check all permissions
                all_perms = admin_user.get_all_permissions()
                self.stdout.write(f'  Total permissions: {len(all_perms)}')
                
            else:
                self.stdout.write('  ❌ Admin user not found')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error checking admin user: {str(e)}')

    def provide_recommendations(self):
        self.stdout.write('\n💡 RECOMMENDATIONS:')
        
        # Check if setup command needs to be run
        total_users = User.objects.count()
        total_groups = Group.objects.count()
        
        if total_users <= 1 and total_groups <= 8:
            self.stdout.write('  🚀 Run: python manage.py setup_production_data')
            self.stdout.write('     This will import all SQLite data and set up permissions')
        
        # Check if just permissions need fixing
        admin_user = User.objects.filter(username='admin').first()
        if admin_user and not admin_user.has_perm('patients.can_register_patients'):
            self.stdout.write('  🔧 Run: python manage.py setup_production_data --skip-import')
            self.stdout.write('     This will fix permissions without importing data')
        
        # Check if groups need permissions
        reg_clerks = Group.objects.filter(name='Registration Clerks').first()
        if reg_clerks and reg_clerks.permissions.count() == 0:
            self.stdout.write('  ⚙️  Groups exist but have no permissions')
            self.stdout.write('     Run setup command to assign permissions to groups')
        
        self.stdout.write('\n🔍 For immediate access:')
        self.stdout.write('  1. Login as admin user')
        self.stdout.write('  2. Go to Django admin -> Groups')
        self.stdout.write('  3. Add users to appropriate groups manually if needed')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('🏥 DIAGNOSIS COMPLETE')
