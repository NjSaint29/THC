# TIKO Health Campaign - Production Deployment Checklist

## Pre-Deployment Checklist

### ✅ **Database Configuration**
- [x] PostgreSQL database created on Render
- [x] Database credentials configured
- [x] DATABASE_URL environment variable set
- [x] Database connection tested

**Database Details:**
- Hostname: `dpg-d25pe8ndiees73eogl8g-a`
- Port: `5432`
- Database: `thc_db`
- Username: `thc_db_user`
- Password: `ULzyd2RToYcaUoMIRhfOQRBl3MZGY9Oe`

### ✅ **Environment Configuration**
- [x] SECRET_KEY configured (generate new for production)
- [x] DEBUG=False set
- [x] ALLOWED_HOSTS includes `thc-1.onrender.com`
- [x] Production security settings enabled
- [x] WhiteNoise configured for static files

### ✅ **Dependencies**
- [x] requirements.txt updated with all production packages
- [x] gunicorn for WSGI server
- [x] whitenoise for static file serving
- [x] psycopg2-binary for PostgreSQL
- [x] dj-database-url for database URL parsing
- [x] python-decouple for environment variables

### ✅ **Security Settings**
- [x] HTTPS redirect enabled
- [x] Security headers configured
- [x] HSTS settings enabled
- [x] Secure cookies configured
- [x] XSS protection enabled
- [x] Content type sniffing protection

### ✅ **Static Files**
- [x] STATIC_ROOT configured
- [x] WhiteNoise middleware added
- [x] Compressed static files storage configured
- [x] collectstatic command in build process

## Deployment Steps

### 1. **Render Web Service Configuration**
```
Name: tiko-health-campaign
Runtime: Python 3
Branch: master
Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
Start Command: gunicorn tiko_health_campaign.wsgi:application
```

### 2. **Environment Variables to Set in Render**
```
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=thc-1.onrender.com
DATABASE_URL=postgresql://thc_db_user:ULzyd2RToYcaUoMIRhfOQRBl3MZGY9Oe@dpg-d25pe8ndiees73eogl8g-a:5432/thc_db
DJANGO_LOG_LEVEL=INFO
```

### 3. **Post-Deployment Tasks**

#### **Initial Setup:**
1. **Automatic Superuser Available**
   - **Username**: `admin`
   - **Email**: `admin@tikohealthcampaign.com`
   - **Password**: `TikoAdmin2025!`
   - **⚠️ CRITICAL**: Change password immediately after first login!

2. **Initial Data Automatically Created**
   - Login to admin panel: `https://thc-1.onrender.com/admin/`
   - Default campaign "TIKO Health Campaign 2025" created
   - Three default locations created
   - Complete lab test formulary with 12 common tests
   - Review and customize as needed

#### **System Configuration:**
1. **Campaign Setup**
   - Create main health campaign
   - Add campaign locations
   - Configure campaign settings

2. **Lab Test Formulary**
   - Add common lab tests
   - Set normal ranges and units
   - Configure test categories

3. **User Management**
   - Create staff accounts for each role
   - Test role-based access
   - Verify dashboard functionality

#### **Testing Checklist:**
- [ ] Admin panel accessible
- [ ] User login/logout working
- [ ] Patient registration functional
- [ ] Consultation creation working
- [ ] Lab order creation working
- [ ] Lab result entry working (both individual and tabular)
- [ ] Search functionality working
- [ ] All role dashboards accessible
- [ ] Static files loading correctly
- [ ] Database operations working
- [ ] SSL certificate active

## Production URLs

- **Main Application**: https://thc-1.onrender.com/
- **Admin Panel**: https://thc-1.onrender.com/admin/
- **Staff Registration**: https://thc-1.onrender.com/accounts/staff/register/
- **API Endpoints**: https://thc-1.onrender.com/api/

## Monitoring & Maintenance

### **Health Checks**
- Monitor application logs in Render dashboard
- Check database connection status
- Verify static file serving
- Monitor response times

### **Regular Tasks**
- Review application logs weekly
- Monitor database performance
- Update dependencies monthly
- Backup database regularly
- Review user access and permissions

### **Performance Monitoring**
- Monitor memory usage
- Check database query performance
- Review static file caching
- Monitor user activity patterns

## Troubleshooting

### **Common Issues**

**Application Won't Start:**
- Check environment variables are set correctly
- Verify DATABASE_URL format
- Check build logs for dependency issues
- Ensure all migrations are applied

**Database Connection Errors:**
- Verify database credentials
- Check database server status
- Ensure database URL is correct
- Test connection from Render shell

**Static Files Not Loading:**
- Verify collectstatic ran successfully
- Check WhiteNoise configuration
- Ensure STATIC_ROOT is set correctly
- Check file permissions

**SSL/HTTPS Issues:**
- Verify domain configuration
- Check ALLOWED_HOSTS setting
- Ensure HTTPS redirect is working
- Verify security headers

### **Support Contacts**
- Render Support: https://render.com/docs
- Django Documentation: https://docs.djangoproject.com/
- Project Repository: https://github.com/NjSaint29/THC

## Security Notes

### **Production Security**
- Never expose DEBUG=True in production
- Keep SECRET_KEY secure and unique
- Regularly update dependencies
- Monitor for security vulnerabilities
- Use strong passwords for all accounts
- Enable two-factor authentication where possible

### **Data Protection**
- Regular database backups
- Secure user data handling
- GDPR compliance considerations
- Patient data privacy protection
- Audit trail maintenance

## Success Criteria

✅ **Deployment Successful When:**
- Application loads without errors
- All user roles can login and access their dashboards
- Patient registration workflow complete
- Consultation and lab order creation working
- Lab result entry (both methods) functional
- Search and filtering working
- Admin panel accessible and functional
- SSL certificate active and HTTPS working
- Database operations performing well
- Static files loading correctly

**🚀 TIKO Health Campaign Management System Ready for Production!**
