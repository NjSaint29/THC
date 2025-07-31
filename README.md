# TIKO Health Campaign Management System

A comprehensive healthcare management system designed for health campaigns, featuring patient registration, consultations, laboratory management, and role-based access control.

## Features

### 🏥 **Core Healthcare Management**
- **Patient Registration & Management** - Complete patient demographics and medical history
- **Consultation Management** - Doctor consultations with vitals, diagnosis, and treatment plans
- **Laboratory Management** - Lab order creation, result entry, and reporting
- **Role-Based Access Control** - Different dashboards and permissions for each user role

### 👥 **User Roles & Dashboards**
- **Registration Clerks** - Patient registration and demographic management
- **Vitals Clerks** - Patient vitals and clinical parameter entry
- **Doctors** - Consultations, diagnosis, prescriptions, and lab orders
- **Lab Technicians** - Laboratory result entry and management
- **Campaign Managers** - Campaign oversight and management
- **Data Analysts** - Reports and analytics
- **Administrators** - System administration and user management

### 🔬 **Laboratory System**
- **Simplified 2-Step Workflow** - Ordered → Completed (no intermediate steps)
- **Tabular Result Entry** - Efficient table-based data entry for multiple tests
- **Individual Result Entry** - Detailed form-based entry for single tests
- **Critical Value Management** - Automatic flagging and handling of critical results
- **Comprehensive Search** - Advanced filtering and search capabilities

### 📊 **Advanced Features**
- **Campaign Management** - Multi-location health campaign coordination
- **Staff Registration** - Public registration pages with role selection
- **Unique ID Generation** - Automatic patient and consultation ID generation
- **Status Tracking** - Complete workflow status management
- **Responsive Design** - Mobile-friendly interface

## Technology Stack

- **Backend**: Django 5.2.4
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **API**: Django REST Framework
- **Deployment**: Render.com ready

## Installation

### Prerequisites
- Python 3.8+
- pip
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/NjSaint29/THC.git
   cd THC
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

7. **Access the Application**
   - Open http://localhost:8000 in your browser
   - Admin panel: http://localhost:8000/admin/

## Deployment

### Render.com Deployment

1. **Connect Repository**
   - Connect your GitHub repository to Render
   - Select "Web Service" deployment

2. **Environment Variables**
   Set the following environment variables in Render:
   ```
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   DATABASE_URL=your-postgresql-database-url
   ALLOWED_HOSTS=your-render-app-url.onrender.com
   ```

3. **Build Command**
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```

4. **Start Command**
   ```bash
   gunicorn tiko_health_campaign.wsgi:application
   ```

## Usage

### Getting Started

1. **Admin Setup**
   - Create campaigns and locations
   - Set up lab test formulary
   - Create user accounts with appropriate roles

2. **Staff Registration**
   - Share registration URLs with staff
   - Staff can self-register with role selection
   - Admins can manage and approve registrations

3. **Patient Workflow**
   - Registration Clerk: Register new patients
   - Vitals Clerk: Record patient vitals
   - Doctor: Conduct consultations and order tests
   - Lab Technician: Enter lab results
   - All roles: View patient information as permitted

### Laboratory Workflow

1. **Lab Order Creation**
   - Doctors create lab orders during consultations
   - Orders appear in lab technician dashboard

2. **Result Entry Options**
   - **Individual Entry**: Detailed form for single test
   - **Table Entry**: Efficient table format for multiple tests

3. **Result Viewing**
   - Results immediately available to doctors
   - Integrated display in consultation and patient views

## Project Structure

```
tiko_health_campaign/
├── accounts/           # User management and authentication
├── campaigns/          # Campaign and location management
├── consultations/      # Medical consultations and lab orders
├── laboratory/         # Laboratory management system
├── patients/           # Patient registration and management
├── pharmacy/           # Pharmacy management (future)
├── reports/            # Reporting and analytics
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── media/              # User uploaded files
└── tiko_health_campaign/  # Main project settings
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the GitHub repository.

## Changelog

### Latest Updates
- ✅ Simplified laboratory workflow (2-step process)
- ✅ Tabular lab result entry system
- ✅ Enhanced search and filtering
- ✅ Role-based dashboard improvements
- ✅ Critical value management
- ✅ Comprehensive error handling
- ✅ Mobile-responsive design
- ✅ Production deployment ready
