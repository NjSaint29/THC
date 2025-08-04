"""
Comprehensive lab order creation debugging command
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from consultations.models import Consultation, LabOrder
from consultations.forms import LabOrderFormSet, LabOrderForm
from campaigns.models import LabTest
from patients.models import Patient

User = get_user_model()


class Command(BaseCommand):
    help = 'Debug lab order creation issues comprehensively'

    def handle(self, *args, **options):
        self.stdout.write('🔬 COMPREHENSIVE LAB ORDER DEBUG')
        self.stdout.write('=' * 50)
        
        # Step 1: Check model structure
        self.check_model_structure()
        
        # Step 2: Check form structure
        self.check_form_structure()
        
        # Step 3: Test formset creation
        self.test_formset_creation()
        
        # Step 4: Test manual lab order creation
        self.test_manual_lab_order_creation()
        
        # Step 5: Test form submission simulation
        self.test_form_submission_simulation()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('🏥 LAB ORDER DEBUG COMPLETE')

    def check_model_structure(self):
        self.stdout.write('\n📋 CHECKING MODEL STRUCTURE:')
        self.stdout.write('-' * 30)
        
        # Check LabOrder model fields
        self.stdout.write('  LabOrder Model Fields:')
        for field in LabOrder._meta.fields:
            field_info = f'    - {field.name}: {field.__class__.__name__}'
            if hasattr(field, 'null'):
                field_info += f' (null={field.null}, blank={field.blank})'
            if hasattr(field, 'default'):
                field_info += f' (default={field.default})'
            self.stdout.write(field_info)
        
        # Check relationships
        self.stdout.write('\n  LabOrder Relationships:')
        for field in LabOrder._meta.fields:
            if hasattr(field, 'related_model') and field.related_model:
                self.stdout.write(f'    - {field.name} -> {field.related_model.__name__}')
        
        # Check if doctor field exists
        has_doctor_field = any(field.name == 'doctor' for field in LabOrder._meta.fields)
        self.stdout.write(f'\n  Has doctor field: {"✅" if has_doctor_field else "❌"}')

    def check_form_structure(self):
        self.stdout.write('\n📝 CHECKING FORM STRUCTURE:')
        self.stdout.write('-' * 30)
        
        # Check LabOrderForm fields
        form = LabOrderForm()
        self.stdout.write('  LabOrderForm Fields:')
        for field_name, field in form.fields.items():
            self.stdout.write(f'    - {field_name}: {field.__class__.__name__} (required={field.required})')
        
        # Check LabOrderFormSet configuration
        self.stdout.write('\n  LabOrderFormSet Configuration:')
        self.stdout.write(f'    - Model: {LabOrderFormSet.model.__name__}')
        self.stdout.write(f'    - Form: {LabOrderFormSet.form.__name__}')
        self.stdout.write(f'    - Extra forms: {LabOrderFormSet.extra}')
        self.stdout.write(f'    - Can delete: {LabOrderFormSet.can_delete}')
        
        # Check formset fields
        if hasattr(LabOrderFormSet, 'fields'):
            self.stdout.write(f'    - Fields: {LabOrderFormSet.fields}')

    def test_formset_creation(self):
        self.stdout.write('\n🧪 TESTING FORMSET CREATION:')
        self.stdout.write('-' * 30)
        
        try:
            # Get test data
            patient = Patient.objects.first()
            if not patient:
                self.stdout.write('  ❌ No patient found for testing')
                return
            
            # Create empty formset
            formset = LabOrderFormSet(
                prefix='lab_orders',
                form_kwargs={'campaign': patient.campaign}
            )
            
            self.stdout.write(f'  ✅ Formset created successfully')
            self.stdout.write(f'    - Total forms: {len(formset.forms)}')
            self.stdout.write(f'    - Management form: {formset.management_form}')
            
            # Check first form
            if formset.forms:
                first_form = formset.forms[0]
                self.stdout.write(f'    - First form fields: {list(first_form.fields.keys())}')
                
                # Check if form has campaign data
                if hasattr(first_form, 'campaign'):
                    self.stdout.write(f'    - Form has campaign: {first_form.campaign}')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Formset creation failed: {str(e)}')

    def test_manual_lab_order_creation(self):
        self.stdout.write('\n🔧 TESTING MANUAL LAB ORDER CREATION:')
        self.stdout.write('-' * 30)
        
        try:
            # Get test data
            patient = Patient.objects.first()
            doctor = User.objects.filter(role='doctor').first()
            lab_test = LabTest.objects.first()
            
            if not all([patient, doctor, lab_test]):
                missing = []
                if not patient: missing.append('patient')
                if not doctor: missing.append('doctor')
                if not lab_test: missing.append('lab_test')
                self.stdout.write(f'  ❌ Missing test data: {", ".join(missing)}')
                return
            
            # Create consultation
            consultation = Consultation.objects.create(
                patient=patient,
                doctor=doctor,
                chief_complaint='Test complaint for lab order debugging',
                working_diagnosis='Test diagnosis',
                treatment_plan='Order lab tests for debugging'
            )
            
            self.stdout.write(f'  ✅ Test consultation created: ID {consultation.id}')
            
            # Test 1: Create lab order with formulary test
            lab_order1 = LabOrder.objects.create(
                consultation=consultation,
                lab_test=lab_test,
                urgency='routine',
                clinical_indication='Test indication',
                lab_status='ordered'
            )
            
            self.stdout.write(f'  ✅ Lab order with formulary test created: ID {lab_order1.id}')
            self.stdout.write(f'    - Test name: {lab_order1.get_test_name()}')
            self.stdout.write(f'    - Status: {lab_order1.lab_status}')
            
            # Test 2: Create lab order with custom test name
            lab_order2 = LabOrder.objects.create(
                consultation=consultation,
                custom_test_name='Custom Blood Test',
                urgency='urgent',
                clinical_indication='Custom test indication',
                lab_status='ordered'
            )
            
            self.stdout.write(f'  ✅ Lab order with custom test created: ID {lab_order2.id}')
            self.stdout.write(f'    - Test name: {lab_order2.get_test_name()}')
            self.stdout.write(f'    - Status: {lab_order2.lab_status}')
            
            # Verify consultation has lab orders
            orders_count = consultation.lab_orders.count()
            self.stdout.write(f'  ✅ Consultation has {orders_count} lab orders')
            
            # Clean up
            lab_order1.delete()
            lab_order2.delete()
            consultation.delete()
            
        except Exception as e:
            self.stdout.write(f'  ❌ Manual lab order creation failed: {str(e)}')

    def test_form_submission_simulation(self):
        self.stdout.write('\n📤 TESTING FORM SUBMISSION SIMULATION:')
        self.stdout.write('-' * 30)
        
        try:
            # Get test data
            patient = Patient.objects.first()
            doctor = User.objects.filter(role='doctor').first()
            lab_test = LabTest.objects.first()
            
            if not all([patient, doctor, lab_test]):
                self.stdout.write('  ❌ Missing test data for simulation')
                return
            
            # Check if lab test is available in patient's campaign
            campaign_lab_tests = patient.campaign.lab_tests.all()
            self.stdout.write(f'  📋 Campaign lab tests found: {campaign_lab_tests.count()}')

            if campaign_lab_tests.count() == 0:
                self.stdout.write('  ⚠️  No lab tests available in patient campaign')
                # Use any available lab test for testing
                available_lab_test_obj = LabTest.objects.first()
                if not available_lab_test_obj:
                    self.stdout.write('  ❌ No lab tests available at all')
                    return
            else:
                available_lab_test = campaign_lab_tests.first()
                available_lab_test_obj = available_lab_test.lab_test

            # Simulate POST data for lab order formset
            post_data = {
                # Management form data
                'lab_orders-TOTAL_FORMS': '2',
                'lab_orders-INITIAL_FORMS': '0',
                'lab_orders-MIN_NUM_FORMS': '0',
                'lab_orders-MAX_NUM_FORMS': '1000',

                # First lab order - using formulary test from campaign
                'lab_orders-0-test_name': available_lab_test_obj.name,
                'lab_orders-0-common_test': str(available_lab_test_obj.id),
                'lab_orders-0-urgency': 'routine',
                'lab_orders-0-clinical_indication': 'Test indication 1',
                'lab_orders-0-notes': 'Test notes 1',

                # Second lab order - using custom test name
                'lab_orders-1-test_name': 'Custom Liver Function Test',
                'lab_orders-1-common_test': '',
                'lab_orders-1-urgency': 'urgent',
                'lab_orders-1-clinical_indication': 'Test indication 2',
                'lab_orders-1-notes': 'Test notes 2',
            }
            
            self.stdout.write('  📋 Simulated POST data created')
            
            # Create formset with POST data
            formset = LabOrderFormSet(
                data=post_data,
                prefix='lab_orders',
                form_kwargs={'campaign': patient.campaign}
            )
            
            self.stdout.write(f'  📝 Formset validation: {"✅ Valid" if formset.is_valid() else "❌ Invalid"}')
            
            if not formset.is_valid():
                self.stdout.write('  📋 Formset errors:')
                for i, form in enumerate(formset.forms):
                    if form.errors:
                        self.stdout.write(f'    Form {i}: {form.errors}')
                if formset.non_form_errors():
                    self.stdout.write(f'    Non-form errors: {formset.non_form_errors()}')
            else:
                # Test saving the formset
                consultation = Consultation.objects.create(
                    patient=patient,
                    doctor=doctor,
                    chief_complaint='Test complaint for formset',
                    working_diagnosis='Test diagnosis',
                    treatment_plan='Test treatment'
                )
                
                formset.instance = consultation
                lab_orders = formset.save()
                
                self.stdout.write(f'  ✅ Formset saved successfully')
                self.stdout.write(f'    - Lab orders created: {len(lab_orders)}')
                
                for i, lab_order in enumerate(lab_orders):
                    self.stdout.write(f'    - Order {i+1}: {lab_order.get_test_name()} ({lab_order.lab_status})')
                
                # Clean up
                for lab_order in lab_orders:
                    lab_order.delete()
                consultation.delete()
            
        except Exception as e:
            self.stdout.write(f'  ❌ Form submission simulation failed: {str(e)}')
            import traceback
            self.stdout.write(f'  📋 Traceback: {traceback.format_exc()}')
