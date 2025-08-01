"""
Test the complete healthcare workflow
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the complete healthcare workflow'

    def handle(self, *args, **options):
        self.stdout.write('🧪 TESTING COMPLETE HEALTHCARE WORKFLOW')
        self.stdout.write('=' * 50)
        
        # Test 1: User login and redirects
        self.test_user_logins()
        
        # Test 2: Permission access
        self.test_permission_access()
        
        # Test 3: Lab order creation
        self.test_lab_order_creation()
        
        # Test 4: Complete workflow
        self.test_complete_workflow()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('🏥 WORKFLOW TESTING COMPLETE')

    def test_user_logins(self):
        self.stdout.write('\n🔐 TESTING USER LOGINS AND REDIRECTS:')
        self.stdout.write('-' * 40)
        
        # Test different user roles
        test_roles = ['admin', 'doctor', 'registration_clerk', 'lab_technician']
        
        for role in test_roles:
            try:
                user = User.objects.filter(role=role).first()
                if user:
                    client = Client()
                    
                    # Test login
                    login_response = client.post('/accounts/login/', {
                        'username': user.username,
                        'password': 'TikoAdmin2025!' if user.username == 'admin' else 'defaultpass'
                    })
                    
                    if login_response.status_code == 302:  # Redirect after login
                        self.stdout.write(f'  ✅ {role} ({user.username}): Login successful')
                        
                        # Check redirect location
                        redirect_url = login_response.url
                        self.stdout.write(f'    → Redirected to: {redirect_url}')
                    else:
                        self.stdout.write(f'  ❌ {role} ({user.username}): Login failed')
                        
                else:
                    self.stdout.write(f'  ⚠️  {role}: No user found')
                    
            except Exception as e:
                self.stdout.write(f'  ❌ {role}: Error - {str(e)}')

    def test_permission_access(self):
        self.stdout.write('\n🔒 TESTING PERMISSION ACCESS:')
        self.stdout.write('-' * 40)
        
        # Test critical URLs for different roles
        test_cases = [
            ('admin', '/patients/register/', 'Patient Registration'),
            ('doctor', '/consultations/patient-search/', 'Consultation Search'),
            ('registration_clerk', '/patients/register/', 'Patient Registration'),
            ('lab_technician', '/laboratory/dashboard/', 'Lab Dashboard'),
        ]
        
        for role, url, description in test_cases:
            try:
                user = User.objects.filter(role=role).first()
                if user:
                    client = Client()
                    client.force_login(user)
                    
                    response = client.get(url)
                    
                    if response.status_code == 200:
                        self.stdout.write(f'  ✅ {role}: {description} - Access granted')
                    elif response.status_code == 403:
                        self.stdout.write(f'  ❌ {role}: {description} - 403 Forbidden')
                    elif response.status_code == 404:
                        self.stdout.write(f'  ⚠️  {role}: {description} - 404 Not Found')
                    else:
                        self.stdout.write(f'  ⚠️  {role}: {description} - Status {response.status_code}')
                        
                else:
                    self.stdout.write(f'  ⚠️  {role}: No user found')
                    
            except Exception as e:
                self.stdout.write(f'  ❌ {role}: Error - {str(e)}')

    def test_lab_order_creation(self):
        self.stdout.write('\n🧪 TESTING LAB ORDER CREATION:')
        self.stdout.write('-' * 40)
        
        try:
            from consultations.models import Consultation, LabOrder
            from campaigns.models import LabTest
            from patients.models import Patient
            
            # Get test data
            doctor = User.objects.filter(role='doctor').first()
            patient = Patient.objects.first()
            lab_test = LabTest.objects.first()
            
            if doctor and patient and lab_test:
                # Create test consultation
                consultation = Consultation.objects.create(
                    patient=patient,
                    doctor=doctor,
                    chief_complaint='Test complaint for lab order',
                    history_of_present_illness='Test history',
                    diagnosis='Test diagnosis requiring lab work',
                    treatment_plan='Order lab tests'
                )
                
                # Create lab order
                lab_order = LabOrder.objects.create(
                    consultation=consultation,
                    lab_test=lab_test,
                    doctor=doctor,
                    urgency='routine',
                    clinical_indication='Test indication',
                    lab_status='ordered'
                )
                
                self.stdout.write(f'  ✅ Lab Order Created: ID {lab_order.id}')
                self.stdout.write(f'    - Test: {lab_order.get_test_name()}')
                self.stdout.write(f'    - Status: {lab_order.lab_status}')
                self.stdout.write(f'    - Doctor: {lab_order.doctor.username}')
                
                # Verify relationship
                orders_count = consultation.lab_orders.count()
                self.stdout.write(f'    - Consultation has {orders_count} lab orders')
                
                # Clean up
                lab_order.delete()
                consultation.delete()
                
            else:
                missing = []
                if not doctor: missing.append('doctor')
                if not patient: missing.append('patient')
                if not lab_test: missing.append('lab_test')
                self.stdout.write(f'  ❌ Missing test data: {", ".join(missing)}')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Lab order creation failed: {str(e)}')

    def test_complete_workflow(self):
        self.stdout.write('\n🏥 TESTING COMPLETE WORKFLOW:')
        self.stdout.write('-' * 40)
        
        try:
            # Test patient registration
            self.test_patient_registration()
            
            # Test consultation creation
            self.test_consultation_creation()
            
            # Test lab workflow
            self.test_lab_workflow()
            
        except Exception as e:
            self.stdout.write(f'  ❌ Workflow test failed: {str(e)}')

    def test_patient_registration(self):
        self.stdout.write('\n  📝 Patient Registration Test:')
        
        try:
            registration_clerk = User.objects.filter(role='registration_clerk').first()
            if registration_clerk:
                client = Client()
                client.force_login(registration_clerk)
                
                # Test access to registration page
                response = client.get('/patients/register/')
                
                if response.status_code == 200:
                    self.stdout.write('    ✅ Registration page accessible')
                else:
                    self.stdout.write(f'    ❌ Registration page error: {response.status_code}')
                    
            else:
                self.stdout.write('    ⚠️  No registration clerk found')
                
        except Exception as e:
            self.stdout.write(f'    ❌ Registration test failed: {str(e)}')

    def test_consultation_creation(self):
        self.stdout.write('\n  👩‍⚕️ Consultation Creation Test:')
        
        try:
            doctor = User.objects.filter(role='doctor').first()
            if doctor:
                client = Client()
                client.force_login(doctor)
                
                # Test access to consultation search
                response = client.get('/consultations/patient-search/')
                
                if response.status_code == 200:
                    self.stdout.write('    ✅ Consultation search accessible')
                else:
                    self.stdout.write(f'    ❌ Consultation search error: {response.status_code}')
                    
            else:
                self.stdout.write('    ⚠️  No doctor found')
                
        except Exception as e:
            self.stdout.write(f'    ❌ Consultation test failed: {str(e)}')

    def test_lab_workflow(self):
        self.stdout.write('\n  🔬 Lab Workflow Test:')
        
        try:
            lab_tech = User.objects.filter(role='lab_technician').first()
            if lab_tech:
                client = Client()
                client.force_login(lab_tech)
                
                # Test access to lab dashboard
                response = client.get('/laboratory/dashboard/')
                
                if response.status_code == 200:
                    self.stdout.write('    ✅ Lab dashboard accessible')
                elif response.status_code == 404:
                    self.stdout.write('    ⚠️  Lab dashboard URL not found')
                else:
                    self.stdout.write(f'    ❌ Lab dashboard error: {response.status_code}')
                    
            else:
                self.stdout.write('    ⚠️  No lab technician found')
                
        except Exception as e:
            self.stdout.write(f'    ❌ Lab workflow test failed: {str(e)}')
