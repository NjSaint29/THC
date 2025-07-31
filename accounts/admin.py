from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin
    """
    list_display = ('username', 'get_full_name_display', 'email', 'role', 'get_groups_display', 'is_in_correct_group', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff', 'role', 'groups', 'created_at')
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

    def get_groups_display(self, obj):
        """Display user's groups"""
        groups = obj.groups.all()
        if groups:
            return ', '.join([g.name for g in groups])
        return 'No groups'
    get_groups_display.short_description = 'Groups'

    def is_in_correct_group(self, obj):
        """Check if user is in correct group for their role"""
        return obj.is_in_correct_group()
    is_in_correct_group.short_description = 'Correct Group'
    is_in_correct_group.boolean = True

    def save_model(self, request, obj, form, change):
        """Save model - signals will handle group assignment automatically"""
        super().save_model(request, obj, form, change)

        # The post_save signal will automatically handle group assignment
        # No need for manual group assignment here


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
