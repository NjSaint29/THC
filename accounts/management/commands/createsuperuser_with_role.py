from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import UserRole
import getpass


class Command(BaseCommand):
    help = 'Create a superuser with role assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            help='Username for the superuser',
        )
        parser.add_argument(
            '--email',
            help='Email for the superuser',
        )
        parser.add_argument(
            '--first_name',
            help='First name for the superuser',
        )
        parser.add_argument(
            '--last_name',
            help='Last name for the superuser',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get username
        username = options.get('username')
        if not username:
            username = input('Username: ')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'Error: Username "{username}" is already taken.')
            )
            return
        
        # Get email
        email = options.get('email')
        if not email:
            email = input('Email address: ')
        
        # Get first name
        first_name = options.get('first_name')
        if not first_name:
            first_name = input('First name: ')
        
        # Get last name
        last_name = options.get('last_name')
        if not last_name:
            last_name = input('Last name: ')
        
        # Get password
        password = None
        while not password:
            password = getpass.getpass('Password: ')
            password2 = getpass.getpass('Password (again): ')
            
            if password != password2:
                self.stdout.write(
                    self.style.ERROR("Error: Your passwords didn't match.")
                )
                password = None
                continue
            
            if len(password) < 8:
                self.stdout.write(
                    self.style.ERROR("Error: Password must be at least 8 characters long.")
                )
                password = None
                continue
        
        try:
            # Create the superuser with admin role
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.ADMIN,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            # Assign to Administrators group if it exists
            try:
                admin_group = Group.objects.get(name='Administrators')
                user.groups.add(admin_group)
                self.stdout.write(
                    self.style.SUCCESS(f'User assigned to Administrators group.')
                )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        'Warning: Administrators group does not exist. '
                        'Run "python manage.py setup_permissions" to create groups.'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Superuser "{username}" created successfully with Admin role!'
                )
            )
            
            # Display user information
            self.stdout.write('\nUser Details:')
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Name: {user.get_full_name()}')
            self.stdout.write(f'Role: {user.get_role_display()}')
            self.stdout.write(f'Staff: {user.is_staff}')
            self.stdout.write(f'Superuser: {user.is_superuser}')
            self.stdout.write(f'Active: {user.is_active}')
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Validation error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
