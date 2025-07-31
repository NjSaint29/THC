"""
Management command to fix user permissions and group assignments
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from accounts.signals import ROLE_GROUP_MAPPING, ensure_user_has_correct_permissions

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix user permissions and group assignments based on their roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Fix permissions for a specific user',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        username = options.get('username')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        if username:
            # Fix specific user
            try:
                user = User.objects.get(username=username)
                self.fix_user_permissions(user, dry_run)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {username} not found'))
                return
        else:
            # Fix all users
            users = User.objects.all()
            self.stdout.write(f'Processing {users.count()} users...')
            
            fixed_count = 0
            for user in users:
                if self.fix_user_permissions(user, dry_run):
                    fixed_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Fixed permissions for {fixed_count} users')
            )

    def fix_user_permissions(self, user, dry_run=False):
        """
        Fix permissions for a single user
        """
        changes_made = False
        
        self.stdout.write(f'\nProcessing user: {user.username}')
        self.stdout.write(f'  Current role: {user.role or "None"}')
        
        # Get current groups
        current_groups = list(user.groups.all())
        current_group_names = [g.name for g in current_groups]
        self.stdout.write(f'  Current groups: {current_group_names}')
        
        if not user.role:
            self.stdout.write(self.style.WARNING(f'  User {user.username} has no role assigned'))
            return False
        
        # Get expected group
        expected_group_name = ROLE_GROUP_MAPPING.get(user.role)
        if not expected_group_name:
            self.stdout.write(self.style.ERROR(f'  No group mapping for role: {user.role}'))
            return False
        
        try:
            expected_group = Group.objects.get(name=expected_group_name)
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'  Group {expected_group_name} does not exist'))
            return False
        
        # Check if user is in correct group
        if expected_group not in current_groups:
            self.stdout.write(self.style.WARNING(f'  Adding user to group: {expected_group_name}'))
            if not dry_run:
                user.groups.add(expected_group)
            changes_made = True
        
        # Remove from incorrect role-based groups
        role_based_groups = Group.objects.filter(name__in=ROLE_GROUP_MAPPING.values())
        for group in current_groups:
            if group in role_based_groups and group.name != expected_group_name:
                self.stdout.write(self.style.WARNING(f'  Removing user from group: {group.name}'))
                if not dry_run:
                    user.groups.remove(group)
                changes_made = True
        
        # Handle admin users
        if user.role == 'admin':
            if not user.is_staff:
                self.stdout.write(self.style.WARNING(f'  Setting is_staff=True for admin user'))
                if not dry_run:
                    user.is_staff = True
                changes_made = True
            
            if not user.is_superuser:
                self.stdout.write(self.style.WARNING(f'  Setting is_superuser=True for admin user'))
                if not dry_run:
                    user.is_superuser = True
                changes_made = True
            
            if changes_made and not dry_run:
                user.save()
        
        # Check permissions
        if not dry_run:
            group_permissions = expected_group.permissions.all()
            user_permissions = user.get_all_permissions()
            expected_permissions = set(f'{p.content_type.app_label}.{p.codename}' for p in group_permissions)
            
            missing_permissions = expected_permissions - user_permissions
            if missing_permissions:
                self.stdout.write(self.style.WARNING(f'  User missing permissions: {missing_permissions}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  User has all expected permissions'))
        
        if changes_made:
            self.stdout.write(self.style.SUCCESS(f'  Fixed permissions for {user.username}'))
        else:
            self.stdout.write(f'  No changes needed for {user.username}')
        
        return changes_made
