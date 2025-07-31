# TIKO Health Campaign - Deployment Guide

## Render.com Deployment Instructions

### Prerequisites
- GitHub repository: https://github.com/NjSaint29/THC.git
- Render.com account

### Step 1: Create Web Service on Render

1. **Login to Render.com**
   - Go to https://render.com
   - Sign in with your GitHub account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub account if not already connected
   - Select the repository: `NjSaint29/THC`
   - Click "Connect"

### Step 2: Configure Web Service

**Basic Settings:**
- **Name**: `tiko-health-campaign` (or your preferred name)
- **Region**: Choose closest to your users
- **Branch**: `master`
- **Runtime**: `Python 3`

**Build & Deploy Settings:**
- **Build Command**: 
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
  ```
- **Start Command**: 
  ```bash
  gunicorn tiko_health_campaign.wsgi:application
  ```

### Step 3: Environment Variables

Add the following environment variables in Render dashboard:

**Required Variables:**
```
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=thc-1.onrender.com
DATABASE_URL=postgresql://thc_db_user:ULzyd2RToYcaUoMIRhfOQRBl3MZGY9Oe@dpg-d25pe8ndiees73eogl8g-a:5432/thc_db
```

**Optional Variables:**
```
DJANGO_SETTINGS_MODULE=tiko_health_campaign.settings
```

### Step 4: Database Setup

**Option A: Use Render PostgreSQL (Recommended)**
1. Create a new PostgreSQL database on Render
2. Copy the database URL from Render dashboard
3. Set it as `DATABASE_URL` environment variable

**Option B: External Database**
1. Use any PostgreSQL provider (AWS RDS, Google Cloud SQL, etc.)
2. Get the connection URL
3. Set it as `DATABASE_URL` environment variable

### Step 5: Deploy

1. **Click "Create Web Service"**
   - Render will automatically start building and deploying
   - Monitor the build logs for any errors

2. **Wait for Deployment**
   - Initial deployment may take 5-10 minutes
   - Watch the logs for successful completion

3. **Access Your Application**
   - Once deployed, access via: `https://your-app-name.onrender.com`

### Step 6: Post-Deployment Setup

1. **Create Superuser**
   - Go to Render dashboard → Shell
   - Run: `python manage.py createsuperuser`
   - Follow prompts to create admin user

2. **Initial Data Setup**
   - Login to admin panel: `https://your-app-name.onrender.com/admin/`
   - Create campaigns, locations, and lab test formulary
   - Set up initial user accounts

### Environment Variables Explained

**SECRET_KEY**: Django secret key for security
- Generate at: https://djecrety.ir/
- Keep it secret and unique

**DEBUG**: Should be False in production
- Set to `False` for security

**ALLOWED_HOSTS**: Domains allowed to serve the app
- Set to your Render app URL: `thc-1.onrender.com`

**DATABASE_URL**: PostgreSQL connection string
- Format: `postgresql://username:password@hostname:port/database_name`
- Provided by Render PostgreSQL service

### Troubleshooting

**Build Fails:**
- Check requirements.txt for correct package versions
- Ensure all dependencies are listed
- Check build logs for specific errors

**App Won't Start:**
- Verify start command is correct
- Check environment variables are set
- Review application logs

**Database Errors:**
- Ensure DATABASE_URL is correct
- Check database is accessible
- Run migrations: `python manage.py migrate`

**Static Files Not Loading:**
- Ensure collectstatic runs in build command
- Check STATIC_URL and STATIC_ROOT settings
- Verify WhiteNoise is installed

### Production Checklist

- [ ] SECRET_KEY is set and secure
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configured
- [ ] Database connected and migrated
- [ ] Static files collected
- [ ] Superuser created
- [ ] Initial data loaded
- [ ] SSL certificate active (automatic on Render)
- [ ] Custom domain configured (if needed)

### Monitoring & Maintenance

**Health Checks:**
- Render automatically monitors app health
- Check logs regularly for errors
- Monitor database performance

**Updates:**
- Push changes to GitHub master branch
- Render will automatically redeploy
- Monitor deployment logs

**Backups:**
- Set up regular database backups
- Export important data periodically
- Keep local development environment updated

### Support

For deployment issues:
- Check Render documentation: https://render.com/docs
- Review Django deployment guide: https://docs.djangoproject.com/en/5.2/howto/deployment/
- Contact support through GitHub issues

### Security Notes

- Never commit sensitive data to repository
- Use environment variables for all secrets
- Regularly update dependencies
- Monitor for security vulnerabilities
- Enable HTTPS (automatic on Render)
- Set up proper user permissions

### Performance Optimization

- Use database connection pooling
- Enable caching for static content
- Optimize database queries
- Monitor application performance
- Scale resources as needed

Your TIKO Health Campaign Management System is now ready for production use!
