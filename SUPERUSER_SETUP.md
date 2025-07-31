# Tiko Health Campaign - Superuser Setup Guide

## Creating a Superuser Account

Due to our custom User model with role requirements, you need to use our custom command to create superuser accounts.

### Method 1: Interactive Command (Recommended)

```bash
python manage.py createsuperuser_with_role
```

This will prompt you for:
- Username
- Email address
- First name
- Last name
- Password (twice for confirmation)

### Method 2: Non-Interactive Command

```bash
python manage.py createsuperuser_with_role --username=admin --email=admin@example.com --first_name=Admin --last_name=User
```

You'll still be prompted for the password for security.

### Method 3: Fully Non-Interactive (for scripts)

```bash
echo "from accounts.models import User, UserRole; User.objects.create_superuser('admin', 'admin@example.com', 'your_password', first_name='Admin', last_name='User', role=UserRole.ADMIN)" | python manage.py shell
```

## Setting Up Permissions

After creating your first superuser, run this command to set up user groups and permissions:

```bash
python manage.py setup_permissions
```

This creates the following groups with appropriate permissions:
- **Registration Clerks** - Can register patients and manage demographics
- **Vitals Clerks** - Can record clinical parameters
- **Doctors** - Can conduct consultations, order tests, and prescribe medications
- **Lab Technicians** - Can process lab orders and enter results

## Default Superuser Credentials

If you created a superuser using the examples above:
- **Username:** superadmin
- **Email:** superadmin@tikohealth.com
- **Password:** [whatever you set]
- **Role:** Administrator

## Troubleshooting

### Error: "NOT NULL constraint failed: accounts_user.role"

This happens when using the default Django `createsuperuser` command. Always use our custom command:
```bash
python manage.py createsuperuser_with_role
```

### Error: "Username already taken"

Choose a different username or check existing users:
```bash
python manage.py shell
>>> from accounts.models import User
>>> User.objects.all().values_list('username', flat=True)
```

### Error: "Administrators group does not exist"

Run the permissions setup command:
```bash
python manage.py setup_permissions
```

## Staff Registration

Once you have a superuser account, you can:

1. **Share the public registration URL** with staff members:
   ```
   http://your-domain.com/accounts/staff/register/
   ```

2. **Manage staff accounts** through the Django admin interface:
   ```
   http://your-domain.com/admin/
   ```

3. **View and edit staff** through the staff management interface:
   ```
   http://your-domain.com/accounts/staff/
   ```

## Next Steps

1. Create your superuser account
2. Set up permissions
3. Log in and test the system
4. Share the staff registration URL with your team
5. Configure campaigns and start using the system

## Security Notes

- Always use strong passwords for superuser accounts
- Regularly review user accounts and permissions
- Monitor the audit logs for suspicious activity
- Keep the staff registration URL secure and only share with authorized personnel
