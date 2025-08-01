#!/usr/bin/env python
"""
Simple script to set up production data after deployment
Run this after the initial deployment to import all SQLite data
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiko_health_campaign.settings')
django.setup()

from django.core.management import call_command

def main():
    print("🚀 Setting up TIKO Health Campaign production data...")
    
    try:
        # Run the setup command
        call_command('setup_production_data')
        print("✅ Production setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Login to admin panel with: admin / TikoAdmin2025!")
        print("2. Change the admin password immediately")
        print("3. Test patient registration and other features")
        print("4. Create additional user accounts as needed")
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        print("\n🔧 Manual setup required:")
        print("1. Login to admin panel with: admin / TikoAdmin2025!")
        print("2. Create user groups manually if needed")
        print("3. Import data using Django admin")
        
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
