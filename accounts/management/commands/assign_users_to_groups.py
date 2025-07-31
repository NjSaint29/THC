from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User, UserRole


class Command(BaseCommand):
    help = 'Assign existing users to groups based on their roles'

    def handle(self, *args, **options):
        self.stdout.write('Assigning users to groups based on their roles...')
        
        # Map roles to group names
        role_group_mapping = {
            UserRole.REGISTRATION_CLERK: 'Registration Clerks',
            UserRole.VITALS_CLERK: 'Vitals Clerks',
            UserRole.DOCTOR: 'Doctors',
            UserRole.LAB_TECHNICIAN: 'Lab Technicians',
            UserRole.CAMPAIGN_MANAGER: 'Campaign Managers',
            UserRole.PHARMACY_CLERK: 'Pharmacy Clerks',
            UserRole.DATA_ANALYST: 'Data Analysts',
            UserRole.ADMIN: 'Administrators',
        }
        
        users_assigned = 0
        users_skipped = 0
        
        for user in User.objects.all():
            group_name = role_group_mapping.get(user.role)
            
            if group_name:
                try:
                    group = Group.objects.get(name=group_name)
                    
                    # Clear existing groups and add the correct one
                    user.groups.clear()
                    user.groups.add(group)
                    
                    self.stdout.write(
                        f'✓ Assigned {user.username} ({user.get_role_display()}) to {group_name}'
                    )
                    users_assigned += 1
                    
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Group "{group_name}" does not exist for user {user.username}. '
                            f'Run "python manage.py setup_permissions" first.'
                        )
                    )
                    users_skipped += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Unknown role "{user.role}" for user {user.username}. Skipping.'
                    )
                )
                users_skipped += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! {users_assigned} users assigned to groups, {users_skipped} skipped.'
            )
        )
        
        # Display current group memberships
        self.stdout.write('\nCurrent group memberships:')
        for group in Group.objects.all():
            users_in_group = group.user_set.all()
            if users_in_group:
                usernames = [u.username for u in users_in_group]
                self.stdout.write(f'- {group.name}: {", ".join(usernames)}')
            else:
                self.stdout.write(f'- {group.name}: (no users)')
