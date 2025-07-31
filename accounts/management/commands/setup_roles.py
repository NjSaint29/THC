from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import UserRole


class Command(BaseCommand):
    help = 'Create user roles and assign permissions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up user roles and permissions...'))
        
        # Create groups and permissions
        UserRole.create_groups_and_permissions()
        
        self.stdout.write(self.style.SUCCESS('Successfully set up user roles and permissions!'))
        
        # Display created groups
        groups = Group.objects.all()
        self.stdout.write(f'\nCreated {groups.count()} groups:')
        for group in groups:
            self.stdout.write(f'  - {group.name} ({group.permissions.count()} permissions)')
