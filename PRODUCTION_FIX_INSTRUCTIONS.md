# 🚨 PRODUCTION FIX: 403 Forbidden Error on Patient Registration

## Problem
Users getting 403 Forbidden error when accessing `/patients/register/` because the post-deployment data setup wasn't executed, so users don't have the required `patients.can_register_patients` permission.

## Immediate Fix (Choose One Method)

### Method 1: Via Render Shell (Recommended)

1. **Access Render Shell**
   - Go to your Render dashboard
   - Navigate to your web service
   - Click "Shell" tab
   - Open a new shell session

2. **Run Diagnostic Command**
   ```bash
   python manage.py diagnose_permissions
   ```
   This will show you exactly what's missing.

3. **Run Emergency Fix**
   ```bash
   python manage.py fix_permissions_now
   ```
   This will immediately fix all permission issues.

4. **Verify Fix**
   - Try accessing: https://thc-1.onrender.com/patients/register/
   - Login with: `admin` / `TikoAdmin2025!`
   - Should work without 403 error

### Method 2: Full Data Import (If You Want All SQLite Data)

1. **Access Render Shell**
   ```bash
   python manage.py setup_production_data
   ```
   This imports all 19 users, 5 patients, 9 consultations from SQLite.

2. **Verify Import**
   ```bash
   python manage.py diagnose_permissions
   ```

### Method 3: Manual Fix via Django Admin

1. **Login to Admin Panel**
   - Go to: https://thc-1.onrender.com/admin/
   - Login with: `admin` / `TikoAdmin2025!`

2. **Create Groups (if missing)**
   - Go to Groups section
   - Create: "Registration Clerks", "Doctors", "Administrators"

3. **Assign Permissions to Groups**
   - Edit "Registration Clerks" group
   - Add permissions: `patients | patient | Can register patients`
   - Add permissions: `patients | patient | Can add patient`
   - Save

4. **Assign Users to Groups**
   - Go to Users section
   - Edit admin user
   - Add to "Administrators" group
   - Save

## Verification Steps

### 1. Check Admin User
```bash
python manage.py shell -c "
from accounts.models import User
admin = User.objects.get(username='admin')
print('Admin has can_register_patients:', admin.has_perm('patients.can_register_patients'))
print('Admin groups:', [g.name for g in admin.groups.all()])
"
```

### 2. Test Patient Registration
- Login as admin: https://thc-1.onrender.com/admin/
- Navigate to: https://thc-1.onrender.com/patients/register/
- Should load without 403 error

### 3. Check All Groups
```bash
python manage.py shell -c "
from django.contrib.auth.models import Group
for group in Group.objects.all():
    print(f'{group.name}: {group.permissions.count()} permissions, {group.user_set.count()} users')
"
```

## Expected Results After Fix

### ✅ Admin User Should Have:
- `is_superuser = True`
- `is_staff = True`
- Member of "Administrators" group
- `patients.can_register_patients` permission
- Access to patient registration page

### ✅ Groups Should Exist:
- Registration Clerks (with patient registration permissions)
- Vitals Clerks (with clinical parameters permissions)
- Doctors (with consultation and lab order permissions)
- Lab Technicians (with lab result permissions)
- Administrators (with all permissions)

### ✅ Permissions Should Work:
- Admin can access all areas
- Registration clerks can register patients
- Doctors can create consultations
- Lab technicians can enter results

## Troubleshooting

### If Commands Don't Work:
1. **Check Python Path**
   ```bash
   which python
   python --version
   ```

2. **Check Django Setup**
   ```bash
   python -c "import django; print(django.VERSION)"
   ```

3. **Manual Permission Assignment**
   - Use Django admin panel
   - Manually create groups and assign permissions
   - Add users to appropriate groups

### If Still Getting 403 Errors:
1. **Clear Browser Cache**
2. **Logout and Login Again**
3. **Check User Session**
   ```bash
   python manage.py shell -c "
   from django.contrib.sessions.models import Session
   print('Active sessions:', Session.objects.count())
   "
   ```

### If Database Issues:
1. **Check Database Connection**
   ```bash
   python manage.py dbshell
   \dt
   \q
   ```

2. **Run Migrations Again**
   ```bash
   python manage.py migrate
   ```

## Prevention for Future Deployments

### Update Build Command:
```bash
pip install -r requirements.txt && 
python manage.py collectstatic --noinput && 
python manage.py migrate && 
python manage.py fix_permissions_now --fix-admin-only
```

This ensures basic permissions are set up during every deployment.

## Support Commands

### Quick Status Check:
```bash
python manage.py diagnose_permissions
```

### Emergency Admin Fix:
```bash
python manage.py fix_permissions_now --fix-admin-only
```

### Full System Setup:
```bash
python manage.py setup_production_data
```

### Reset All Permissions:
```bash
python manage.py fix_permissions_now
```

---

## 🎯 Success Criteria

After running the fix, you should be able to:
1. ✅ Login as admin without issues
2. ✅ Access https://thc-1.onrender.com/patients/register/ without 403 error
3. ✅ See patient registration form
4. ✅ Register a test patient successfully
5. ✅ Access other role-based features

**The 403 Forbidden error should be completely resolved!**
