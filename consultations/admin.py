from django.contrib import admin
from .models import Consultation, LabOrder, Prescription


class LabOrderInline(admin.TabularInline):
    model = LabOrder
    extra = 0
    fields = ('lab_test', 'urgency', 'status', 'clinical_indication')
    readonly_fields = ('ordered_date', 'created_at')


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0
    fields = ('drug', 'dosage', 'frequency', 'duration', 'route', 'status')
    readonly_fields = ('created_at',)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'doctor', 'consultation_date', 'working_diagnosis',
        'status', 'referral_needed', 'created_at'
    )
    list_filter = (
        'status', 'referral_needed', 'consultation_date',
        'doctor', 'patient__campaign'
    )
    search_fields = (
        'patient__patient_id', 'patient__first_name', 'patient__last_name',
        'working_diagnosis', 'chief_complaint'
    )
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Patient & Doctor', {
            'fields': ('patient', 'doctor', 'consultation_date', 'status')
        }),
        ('Chief Complaint & History', {
            'fields': (
                'chief_complaint', 'history_of_present_illness',
                'past_medical_history', 'family_history', 'social_history'
            )
        }),
        ('Physical Examination', {
            'fields': ('general_appearance', 'physical_examination')
        }),
        ('Assessment & Diagnosis', {
            'fields': ('clinical_assessment', 'working_diagnosis', 'treatment_plan')
        }),
        ('Follow-up & Referrals', {
            'fields': (
                'follow_up_instructions', 'referral_needed',
                'referral_to', 'referral_reason'
            )
        }),
        ('Additional Information', {
            'fields': ('additional_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [LabOrderInline, PrescriptionInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new consultation
            obj.doctor = request.user
        super().save_model(request, obj, form, change)


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = (
        'consultation', 'lab_test', 'urgency', 'status',
        'ordered_date', 'created_at'
    )
    list_filter = ('status', 'urgency', 'ordered_date', 'lab_test__category')
    search_fields = (
        'consultation__patient__patient_id',
        'consultation__patient__first_name',
        'consultation__patient__last_name',
        'lab_test__name'
    )
    readonly_fields = ('ordered_date', 'created_at', 'updated_at')

    fieldsets = (
        ('Order Information', {
            'fields': ('consultation', 'lab_test', 'urgency', 'status')
        }),
        ('Clinical Details', {
            'fields': ('clinical_indication', 'notes')
        }),
        ('Timestamps', {
            'fields': ('ordered_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        'consultation', 'drug', 'dosage', 'frequency', 'duration',
        'status', 'dispensed_date', 'created_at'
    )
    list_filter = (
        'status', 'route', 'drug__category', 'dispensed_date', 'created_at'
    )
    search_fields = (
        'consultation__patient__patient_id',
        'consultation__patient__first_name',
        'consultation__patient__last_name',
        'drug__name'
    )
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Prescription Information', {
            'fields': ('consultation', 'drug', 'status')
        }),
        ('Dosage & Instructions', {
            'fields': (
                'dosage', 'frequency', 'duration', 'route',
                'instructions', 'indication'
            )
        }),
        ('Quantity & Refills', {
            'fields': ('quantity', 'refills')
        }),
        ('Dispensing Information', {
            'fields': (
                'dispensed_by', 'dispensed_date', 'dispensed_quantity'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
