from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin
    """
    list_display = ('username', 'get_full_name_display', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff', 'groups', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    ordering = ('-created_at',)
    filter_horizontal = ('groups', 'user_permissions')
    list_per_page = 25

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {
            'fields': ('role', 'phone_number')
        }),
        ('Additional Info', {
            'fields': ('employee_id', 'department'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Role Information', {
            'fields': ('role', 'phone_number')
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def get_full_name_display(self, obj):
        """Display full name or username if no name"""
        return obj.get_full_name() or obj.username
    get_full_name_display.short_description = 'Name'

    def save_model(self, request, obj, form, change):
        """Auto-assign user to appropriate group based on role"""
        super().save_model(request, obj, form, change)

        # Assign to appropriate group
        from django.contrib.auth.models import Group

        # Remove from all groups first
        obj.groups.clear()

        # Map roles to group names
        role_group_mapping = {
            'registration_clerk': 'Registration Clerks',
            'vitals_clerk': 'Vitals Clerks',
            'doctor': 'Doctors',
            'lab_technician': 'Lab Technicians',
            'campaign_manager': 'Campaign Managers',
            'data_analyst': 'Data Analysts',
            'admin': 'Administrators',
        }

        group_name = role_group_mapping.get(obj.role)
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                obj.groups.add(group)
            except Group.DoesNotExist:
                pass


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Audit Log Admin
    """
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'action', 'model_name', 'object_id')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'timestamp', 'ip_address')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
