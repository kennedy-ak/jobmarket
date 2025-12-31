from django.contrib import admin
from .models import Registration, JobListing, MonthlyDraw, Winner

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'region', 'mobile_money_provider', 'registration_date', 'is_active']
    list_filter = ['region', 'mobile_money_provider', 'is_active', 'registration_date']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['registration_date']
    ordering = ['-registration_date']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')
        }),
        ('Location & Payment', {
            'fields': ('region', 'mobile_money_provider')
        }),
        ('Documents', {
            'fields': ('cv_file',)
        }),
        ('System Information', {
            'fields': ('language', 'is_active', 'terms_accepted', 'registration_date'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'job_type', 'salary_range', 'is_active', 'created_date']
    list_filter = ['job_type', 'is_active', 'created_date']
    search_fields = ['title', 'description']
    ordering = ['-created_date']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'description', 'job_type', 'salary_range', 'requirements')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(MonthlyDraw)
class MonthlyDrawAdmin(admin.ModelAdmin):
    list_display = ['draw_month', 'current_participants', 'minimum_participants', 'status', 'winners_selected']
    list_filter = ['status', 'winners_selected', 'draw_month']
    ordering = ['-draw_month']
    readonly_fields = ['created_date']
    
    fieldsets = (
        ('Draw Information', {
            'fields': ('draw_month', 'minimum_participants', 'current_participants')
        }),
        ('Status', {
            'fields': ('status', 'winners_selected')
        }),
        ('System Information', {
            'fields': ('created_date',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    list_display = ['registration', 'monthly_draw', 'prize_type', 'is_claimed', 'claim_date']
    list_filter = ['prize_type', 'is_claimed', 'monthly_draw']
    search_fields = ['registration__first_name', 'registration__last_name', 'registration__email']
    readonly_fields = ['created_date']
    ordering = ['-monthly_draw__draw_month']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('registration', 'monthly_draw')

# Customize admin site header
admin.site.site_header = "Jobmarkt Admin"
admin.site.site_title = "Jobmarkt Admin Portal"
admin.site.index_title = "Welcome to Jobmarkt Administration"
