"""
Comprehensive diagnostic command for all production issues
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test import Client

User = get_user_model()


class Command(BaseCommand):
    help = 'Comprehensive diagnosis of all production issues'

    def handle(self, *args, **options):
        self.stdout.write('🔍 COMPREHENSIVE PRODUCTION DIAGNOSIS')
        self.stdout.write('=' * 60)
        
        # Issue 1: Lab Orders
        self.diagnose_lab_orders()
        
        # Issue 2: Permissions
        self.diagnose_permissions()
        
        # Issue 3: Login Redirects
        self.diagnose_login_redirects()
        
        # Provide comprehensive recommendations
        self.provide_recommendations()

    def diagnose_lab_orders(self):
        self.stdout.write('\n🧪 LAB ORDER DIAGNOSIS:')
        self.stdout.write('-' * 30)
        
        try:
            from consultations.models import Consultation, LabOrder
            from campaigns.models import LabTest
            
            # Check model relationships
            consultations = Consultation.objects.count()
            lab_orders = LabOrder.objects.count()
            lab_tests = LabTest.objects.count()
            
            self.stdout.write(f'  Consultations: {consultations}')
            self.stdout.write(f'  Lab Orders: {lab_orders}')
            self.stdout.write(f'  Lab Tests: {lab_tests}')
            
            # Check recent consultations for lab orders
            recent_consultations = Consultation.objects.all()[:5]
            for consultation in recent_consultations:
                orders = consultation.lab_orders.count()
                self.stdout.write(f'  Consultation {consultation.id}: {orders} lab orders')
            
            # Check LabOrder model structure
            self.stdout.write('\n  LabOrder Model Fields:')
            for field in LabOrder._meta.fields:
                self.stdout.write(f'    - {field.name}: {field.__class__.__name__}')
            
            # Check if LabOrder creation works
            self.test_lab_order_creation()
            
        except Exception as e:
            self.stdout.write(f'  ❌ Error checking lab orders: {str(e)}')

    def test_lab_order_creation(self):
        self.stdout.write('\n  Testing LabOrder Creation:')
        try:
            from consultations.models import Consultation, LabOrder
            from campaigns.models import LabTest
            from patients.models import Patient
            
            # Get test data
            patient = Patient.objects.first()
            doctor = User.objects.filter(role='doctor').first()
            lab_test = LabTest.objects.first()
            
            if patient and doctor and lab_test:
                # Try to create a test consultation with lab order
                consultation = Consultation.objects.create(
                    patient=patient,
                    doctor=doctor,
                    chief_complaint='Test complaint',
                    history_of_present_illness='Test history',
                    diagnosis='Test diagnosis',
                    treatment_plan='Test treatment'
                )
                
                # Try to create lab order
                lab_order = LabOrder.objects.create(
                    consultation=consultation,
                    lab_test=lab_test,
                    doctor=doctor,
                    status='pending'
                )
                
                self.stdout.write(f'    ✅ Test LabOrder created: ID {lab_order.id}')
                
                # Clean up test data
                lab_order.delete()
                consultation.delete()
                
            else:
                self.stdout.write('    ⚠️  Missing test data (patient, doctor, or lab_test)')
                
        except Exception as e:
            self.stdout.write(f'    ❌ LabOrder creation failed: {str(e)}')

    def diagnose_permissions(self):
        self.stdout.write('\n🔐 PERMISSION DIAGNOSIS:')
        self.stdout.write('-' * 30)
        
        # Check critical permissions
        critical_permissions = [
            'patients.can_register_patients',
            'patients.add_patient',
            'patients.view_patient',
            'consultations.can_conduct_consultations',
            'consultations.add_consultation',
            'consultations.view_consultation',
            'consultations.add_laborder',
            'laboratory.can_enter_lab_results',
            'laboratory.add_labresult',
        ]
        
        self.stdout.write('  Critical Permissions Status:')
        for perm_code in critical_permissions:
            app_label, codename = perm_code.split('.')
            try:
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                groups_with_perm = Group.objects.filter(permissions=permission)
                users_with_perm = User.objects.filter(
                    groups__permissions=permission
                ).distinct().count()
                
                group_names = ', '.join([g.name for g in groups_with_perm])
                status = '✅' if users_with_perm > 0 else '❌'
                self.stdout.write(f'    {status} {perm_code}: {users_with_perm} users via [{group_names}]')
                
            except Permission.DoesNotExist:
                self.stdout.write(f'    ❌ {perm_code}: PERMISSION NOT FOUND')
        
        # Check user-group assignments
        self.stdout.write('\n  User-Group Assignments:')
        role_group_mapping = {
            'registration_clerk': 'Registration Clerks',
            'vitals_clerk': 'Vitals Clerks',
            'doctor': 'Doctors',
            'lab_technician': 'Lab Technicians',
            'admin': 'Administrators',
        }
        
        for role, expected_group in role_group_mapping.items():
            users_with_role = User.objects.filter(role=role)
            correctly_assigned = 0
            for user in users_with_role:
                if user.groups.filter(name=expected_group).exists():
                    correctly_assigned += 1
            
            total = users_with_role.count()
            status = '✅' if correctly_assigned == total and total > 0 else '❌'
            self.stdout.write(f'    {status} {role}: {correctly_assigned}/{total} users in {expected_group}')

    def diagnose_login_redirects(self):
        self.stdout.write('\n🔄 LOGIN REDIRECT DIAGNOSIS:')
        self.stdout.write('-' * 30)
        
        # Check if custom login view exists
        try:
            from django.urls import resolve
            from django.conf import settings
            
            # Check LOGIN_REDIRECT_URL setting
            login_redirect = getattr(settings, 'LOGIN_REDIRECT_URL', None)
            self.stdout.write(f'  LOGIN_REDIRECT_URL: {login_redirect}')
            
            # Check if custom login view exists
            try:
                login_url = reverse('login')
                self.stdout.write(f'  Login URL: {login_url}')
                
                # Try to resolve login view
                resolver = resolve(login_url)
                self.stdout.write(f'  Login view: {resolver.func.__name__}')
                
            except Exception as e:
                self.stdout.write(f'  ❌ Login URL resolution error: {str(e)}')
            
            # Check for role-based redirect logic
            self.check_redirect_logic()
            
        except Exception as e:
            self.stdout.write(f'  ❌ Error checking redirects: {str(e)}')

    def check_redirect_logic(self):
        self.stdout.write('\n  Role-Based Redirect Logic:')
        
        # Expected dashboard URLs for each role
        expected_dashboards = {
            'registration_clerk': '/registration/dashboard/',
            'vitals_clerk': '/vitals/dashboard/',
            'doctor': '/doctor/dashboard/',
            'lab_technician': '/lab/dashboard/',
            'campaign_manager': '/campaign/dashboard/',
            'data_analyst': '/analytics/dashboard/',
            'admin': '/admin/dashboard/',
        }
        
        for role, expected_url in expected_dashboards.items():
            try:
                # Try to resolve the URL
                from django.urls import resolve
                resolver = resolve(expected_url)
                self.stdout.write(f'    ✅ {role}: {expected_url} -> {resolver.func.__name__}')
            except Exception:
                self.stdout.write(f'    ❌ {role}: {expected_url} NOT FOUND')

    def provide_recommendations(self):
        self.stdout.write('\n💡 COMPREHENSIVE RECOMMENDATIONS:')
        self.stdout.write('-' * 40)
        
        self.stdout.write('\n🧪 For Lab Order Issues:')
        self.stdout.write('  1. Check consultation form submission logic')
        self.stdout.write('  2. Verify LabOrder model save() method')
        self.stdout.write('  3. Check consultation view for lab order creation')
        self.stdout.write('  4. Test: python manage.py shell')
        self.stdout.write('     >>> from consultations.models import *')
        self.stdout.write('     >>> # Test LabOrder creation manually')
        
        self.stdout.write('\n🔐 For Permission Issues:')
        self.stdout.write('  1. Run: python manage.py fix_permissions_now')
        self.stdout.write('  2. Check: python manage.py diagnose_permissions')
        self.stdout.write('  3. Manually assign users to groups in Django admin')
        self.stdout.write('  4. Verify custom permissions exist')
        
        self.stdout.write('\n🔄 For Login Redirect Issues:')
        self.stdout.write('  1. Implement custom login view with role-based redirects')
        self.stdout.write('  2. Update LOGIN_REDIRECT_URL in settings')
        self.stdout.write('  3. Create dashboard URLs for each role')
        self.stdout.write('  4. Test login flow for each user role')
        
        self.stdout.write('\n🚀 Immediate Actions:')
        self.stdout.write('  1. python manage.py fix_permissions_now')
        self.stdout.write('  2. python manage.py diagnose_all_issues')
        self.stdout.write('  3. Check consultation form in Django admin')
        self.stdout.write('  4. Test complete workflow with test users')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('🏥 COMPREHENSIVE DIAGNOSIS COMPLETE')
