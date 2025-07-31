"""
Django signals for automatic role-to-group assignment and permission management
"""
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

# Role to Group mapping
ROLE_GROUP_MAPPING = {
    'registration_clerk': 'Registration Clerks',
    'vitals_clerk': 'Vitals Clerks',
    'doctor': 'Doctors',
    'lab_technician': 'Lab Technicians',
    'pharmacy_clerk': 'Pharmacy Clerks',
    'campaign_manager': 'Campaign Managers',
    'data_analyst': 'Data Analysts',
    'admin': 'Administrators',
}

# Reverse mapping for group to role
GROUP_ROLE_MAPPING = {v: k for k, v in ROLE_GROUP_MAPPING.items()}


@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    """
    Automatically assign user to appropriate group based on their role
    """
    if not instance.role:
        logger.warning(f"User {instance.username} has no role assigned")
        return
    
    # Get the group name for this role
    group_name = ROLE_GROUP_MAPPING.get(instance.role)
    if not group_name:
        logger.error(f"No group mapping found for role: {instance.role}")
        return
    
    try:
        # Get or create the group
        group, group_created = Group.objects.get_or_create(name=group_name)
        if group_created:
            logger.info(f"Created new group: {group_name}")
        
        # Remove user from all other role-based groups first
        current_groups = instance.groups.filter(name__in=ROLE_GROUP_MAPPING.values())
        for current_group in current_groups:
            if current_group.name != group_name:
                instance.groups.remove(current_group)
                logger.info(f"Removed user {instance.username} from group {current_group.name}")
        
        # Add user to the correct group
        if not instance.groups.filter(name=group_name).exists():
            instance.groups.add(group)
            logger.info(f"Added user {instance.username} to group {group_name}")
        
        # For admin users, ensure they have staff and superuser status
        if instance.role == 'admin':
            if not instance.is_staff:
                instance.is_staff = True
            if not instance.is_superuser:
                instance.is_superuser = True
            # Use update to avoid triggering the signal again
            User.objects.filter(pk=instance.pk).update(
                is_staff=True, 
                is_superuser=True
            )
            logger.info(f"Updated admin user {instance.username} with staff and superuser status")
        
    except Exception as e:
        logger.error(f"Error assigning user {instance.username} to group: {str(e)}")


@receiver(m2m_changed, sender=User.groups.through)
def sync_role_with_groups(sender, instance, action, pk_set, **kwargs):
    """
    Sync user role when groups are manually changed in admin panel
    """
    if action not in ['post_add', 'post_remove']:
        return
    
    try:
        # Get all role-based groups for this user
        user_role_groups = instance.groups.filter(name__in=ROLE_GROUP_MAPPING.values())
        
        if user_role_groups.count() == 1:
            # User has exactly one role-based group, sync the role
            group_name = user_role_groups.first().name
            expected_role = GROUP_ROLE_MAPPING.get(group_name)
            
            if expected_role and instance.role != expected_role:
                # Update role without triggering post_save signal
                User.objects.filter(pk=instance.pk).update(role=expected_role)
                logger.info(f"Updated user {instance.username} role to {expected_role} based on group {group_name}")
        
        elif user_role_groups.count() > 1:
            # User has multiple role-based groups, keep the admin role if present
            if instance.groups.filter(name='Administrators').exists():
                if instance.role != 'admin':
                    User.objects.filter(pk=instance.pk).update(role='admin')
                    logger.info(f"Updated user {instance.username} role to admin due to multiple groups")
            else:
                logger.warning(f"User {instance.username} has multiple role-based groups but no admin group")
        
        elif user_role_groups.count() == 0:
            # User has no role-based groups, clear the role
            if instance.role:
                User.objects.filter(pk=instance.pk).update(role='')
                logger.info(f"Cleared role for user {instance.username} as they have no role-based groups")
    
    except Exception as e:
        logger.error(f"Error syncing role with groups for user {instance.username}: {str(e)}")


def ensure_user_has_correct_permissions(user):
    """
    Utility function to ensure a user has the correct permissions based on their role
    """
    if not user.role:
        return False
    
    group_name = ROLE_GROUP_MAPPING.get(user.role)
    if not group_name:
        return False
    
    try:
        group = Group.objects.get(name=group_name)
        if not user.groups.filter(name=group_name).exists():
            user.groups.add(group)
            logger.info(f"Added user {user.username} to group {group_name}")
            return True
    except Group.DoesNotExist:
        logger.error(f"Group {group_name} does not exist")
        return False
    
    return True


def fix_all_user_permissions():
    """
    Utility function to fix permissions for all existing users
    """
    users_fixed = 0
    for user in User.objects.all():
        if user.role and ensure_user_has_correct_permissions(user):
            users_fixed += 1
    
    logger.info(f"Fixed permissions for {users_fixed} users")
    return users_fixed
