from django.contrib import admin
from .models import Campaign, LabTest, Drug, CampaignLabTest, CampaignDrug


class CampaignLabTestInline(admin.TabularInline):
    model = CampaignLabTest
    extra = 1
    fields = ('lab_test', 'is_default', 'order')


class CampaignDrugInline(admin.TabularInline):
    model = CampaignDrug
    extra = 1
    fields = ('drug', 'is_preferred', 'stock_quantity', 'order')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'health_area', 'status', 'start_date', 'end_date', 'patient_count', 'created_by', 'is_active')
    list_filter = ('status', 'health_area', 'start_date', 'end_date', 'created_by')
    search_fields = ('name', 'health_area', 'description')
    readonly_fields = ('created_at', 'updated_at', 'patient_count', 'is_active', 'days_remaining')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'health_area', 'status')
        }),
        ('Campaign Dates', {
            'fields': ('start_date', 'end_date', 'days_remaining')
        }),
        ('Settings', {
            'fields': ('max_patients', 'consent_text')
        }),
        ('Management', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('patient_count', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    inlines = [CampaignLabTestInline, CampaignDrugInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new campaign
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'category')
        }),
        ('Test Details', {
            'fields': ('normal_range', 'unit')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'strength', 'dosage_form', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'dosage_form', 'is_active', 'created_at')
    search_fields = ('name', 'generic_name')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'category')
        }),
        ('Drug Details', {
            'fields': ('strength', 'dosage_form')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )
