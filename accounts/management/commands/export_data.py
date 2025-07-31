"""
Management command to export all data from SQLite database
"""
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.contrib.auth.models import Group, Permission
from accounts.models import User
from campaigns.models import Campaign, LabTest
from patients.models import Patient, ClinicalParameters
from consultations.models import Consultation, LabOrder, Prescription
from laboratory.models import LabResult


class Command(BaseCommand):
    help = 'Export all data from SQLite database to JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='data_export',
            help='Directory to save exported data files',
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        
        # Create output directory
        import os
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self.stdout.write('Starting data export...')
        
        # Export Groups and Permissions
        self.export_model(Group, f'{output_dir}/groups.json')
        self.export_model(Permission, f'{output_dir}/permissions.json')
        
        # Export Users
        self.export_model(User, f'{output_dir}/users.json')
        
        # Export Campaigns and Lab Tests
        self.export_model(Campaign, f'{output_dir}/campaigns.json')
        self.export_model(LabTest, f'{output_dir}/lab_tests.json')
        
        # Export Patients and Clinical Parameters
        self.export_model(Patient, f'{output_dir}/patients.json')
        self.export_model(ClinicalParameters, f'{output_dir}/clinical_parameters.json')
        
        # Export Consultations, Lab Orders, and Prescriptions
        self.export_model(Consultation, f'{output_dir}/consultations.json')
        self.export_model(LabOrder, f'{output_dir}/lab_orders.json')
        self.export_model(Prescription, f'{output_dir}/prescriptions.json')
        
        # Export Lab Results
        self.export_model(LabResult, f'{output_dir}/lab_results.json')
        
        # Create summary
        self.create_summary(output_dir)
        
        self.stdout.write(
            self.style.SUCCESS(f'Data export completed successfully to {output_dir}/')
        )

    def export_model(self, model_class, filename):
        """Export a model to JSON file"""
        try:
            queryset = model_class.objects.all()
            count = queryset.count()
            
            if count > 0:
                data = serializers.serialize('json', queryset, indent=2)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(data)
                self.stdout.write(f'Exported {count} {model_class.__name__} records to {filename}')
            else:
                self.stdout.write(f'No {model_class.__name__} records to export')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error exporting {model_class.__name__}: {str(e)}')
            )

    def create_summary(self, output_dir):
        """Create a summary of exported data"""
        summary = {
            'export_timestamp': str(datetime.now()),
            'models': {
                'Groups': Group.objects.count(),
                'Permissions': Permission.objects.count(),
                'Users': User.objects.count(),
                'Campaigns': Campaign.objects.count(),
                'LabTests': LabTest.objects.count(),
                'Patients': Patient.objects.count(),
                'ClinicalParameters': ClinicalParameters.objects.count(),
                'Consultations': Consultation.objects.count(),
                'LabOrders': LabOrder.objects.count(),
                'Prescriptions': Prescription.objects.count(),
                'LabResults': LabResult.objects.count(),
            },
            'user_roles': {}
        }
        
        # Add user role breakdown
        for user in User.objects.all():
            role = user.role or 'no_role'
            if role not in summary['user_roles']:
                summary['user_roles'][role] = 0
            summary['user_roles'][role] += 1
        
        with open(f'{output_dir}/export_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        self.stdout.write(f'Created export summary: {output_dir}/export_summary.json')
