from django.contrib import admin
from .models import Patient, ClinicalParameters


class ClinicalParametersInline(admin.StackedInline):
    model = ClinicalParameters
    extra = 0
    fields = (
        ('weight', 'height', 'temperature'),
        ('systolic_bp', 'diastolic_bp', 'heart_rate'),
        ('glucose_type', 'blood_glucose'),
        ('lmp', 'is_pregnant', 'gestational_age', 'age_at_first_pregnancy'),
        'notes',
        ('recorded_by', 'recorded_at', 'updated_at')
    )
    readonly_fields = ('recorded_at', 'updated_at')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'patient_id', 'get_full_name', 'age', 'gender',
        'campaign', 'status', 'registration_date', 'registered_by'
    )
    list_filter = (
        'campaign', 'gender', 'marital_status', 'status',
        'registration_date', 'consent_given'
    )
    search_fields = (
        'patient_id', 'first_name', 'last_name', 'phone_number', 'email'
    )
    readonly_fields = (
        'patient_id', 'registration_date', 'updated_at', 'age_display'
    )

    fieldsets = (
        ('Patient Identification', {
            'fields': ('patient_id', 'campaign', 'status')
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'middle_name', 'last_name'),
                ('date_of_birth', 'age', 'age_display'),
                ('gender', 'marital_status')
            )
        }),
        ('Contact Information', {
            'fields': (
                ('phone_number', 'email'),
                'address',
                ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')
            )
        }),
        ('Campaign & Location', {
            'fields': ('health_area',)
        }),
        ('Consent', {
            'fields': ('consent_given', 'consent_date')
        }),
        ('Registration Details', {
            'fields': ('registered_by', 'registration_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ClinicalParametersInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new patient
            obj.registered_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClinicalParameters)
class ClinicalParametersAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'weight', 'height', 'bmi', 'blood_pressure_display',
        'heart_rate', 'temperature', 'recorded_by', 'recorded_at'
    )
    list_filter = ('recorded_at', 'glucose_type', 'is_pregnant')
    search_fields = ('patient__patient_id', 'patient__first_name', 'patient__last_name')
    readonly_fields = ('bmi', 'bmi_category', 'blood_pressure_display', 'blood_pressure_category', 'recorded_at', 'updated_at')

    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Basic Measurements', {
            'fields': (
                ('weight', 'height', 'bmi', 'bmi_category'),
                'temperature'
            )
        }),
        ('Cardiovascular', {
            'fields': (
                ('systolic_bp', 'diastolic_bp', 'blood_pressure_display', 'blood_pressure_category'),
                'heart_rate'
            )
        }),
        ('Blood Glucose', {
            'fields': ('glucose_type', 'blood_glucose')
        }),
        ('Women\'s Health', {
            'fields': ('lmp', 'is_pregnant', 'gestational_age', 'age_at_first_pregnancy')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Recording Details', {
            'fields': ('recorded_by', 'recorded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new clinical parameters
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
