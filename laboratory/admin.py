from django.contrib import admin
from .models import LabResult, LabWorksheet, LabOrderWorksheet


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = (
        'lab_order', 'patient_id', 'test_name', 'result_value',
        'interpretation', 'status', 'is_critical', 'technician', 'result_date'
    )
    list_filter = (
        'status', 'interpretation', 'is_critical', 'sample_quality',
        'result_date', 'lab_order__lab_test__category'
    )
    search_fields = (
        'lab_order__consultation__patient__patient_id',
        'lab_order__consultation__patient__first_name',
        'lab_order__consultation__patient__last_name',
        'lab_order__lab_test__name',
        'result_value'
    )
    readonly_fields = ('created_at', 'updated_at', 'patient', 'doctor')

    fieldsets = (
        ('Test Information', {
            'fields': ('lab_order', 'patient', 'doctor', 'status')
        }),
        ('Result Details', {
            'fields': (
                'result_value', 'result_unit', 'reference_range',
                'interpretation', 'sample_quality'
            )
        }),
        ('Clinical Information', {
            'fields': ('technician_notes', 'clinical_conclusion', 'test_method')
        }),
        ('Critical Values', {
            'fields': (
                'is_critical', 'critical_notified', 'critical_notified_at'
            )
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('Tracking', {
            'fields': ('technician', 'result_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def patient_id(self, obj):
        return obj.lab_order.consultation.patient.patient_id
    patient_id.short_description = 'Patient ID'

    def test_name(self, obj):
        return obj.lab_order.lab_test.name
    test_name.short_description = 'Test'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new result
            obj.technician = request.user
        super().save_model(request, obj, form, change)


class LabOrderWorksheetInline(admin.TabularInline):
    model = LabOrderWorksheet
    extra = 0
    fields = ('lab_order', 'position')


@admin.register(LabWorksheet)
class LabWorksheetAdmin(admin.ModelAdmin):
    list_display = (
        'worksheet_number', 'test_type', 'technician',
        'sample_count', 'status', 'created_date', 'run_date'
    )
    list_filter = ('status', 'test_type', 'created_date', 'technician')
    search_fields = ('worksheet_number', 'test_type__name')
    readonly_fields = ('created_at', 'updated_at', 'sample_count')

    fieldsets = (
        ('Worksheet Information', {
            'fields': ('worksheet_number', 'test_type', 'technician', 'status')
        }),
        ('Dates', {
            'fields': ('created_date', 'run_date')
        }),
        ('Quality Control', {
            'fields': ('control_results', 'notes')
        }),
        ('Statistics', {
            'fields': ('sample_count',)
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [LabOrderWorksheetInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new worksheet
            obj.technician = request.user
            if not obj.worksheet_number:
                obj.worksheet_number = obj.generate_worksheet_number()
        super().save_model(request, obj, form, change)
