from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os

def validate_cv_file(value):
    file_size = value.size
    max_size = 5 * 1024 * 1024  # 5MB
    
    if file_size > max_size:
        raise ValidationError("File size should not exceed 5MB.")
    
    # Check file extension
    valid_extensions = ['.pdf']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Only PDF files are allowed.")

class Registration(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('nl', 'Dutch'),
    ]
    
    REGION_CHOICES = [
        ('accra', 'Greater Accra Region'),
        ('ashanti', 'Ashanti Region'),
        ('eastern', 'Eastern Region'),
        ('central', 'Central Region'),
        ('western', 'Western Region'),
        ('volta', 'Volta Region'),
        ('other', 'Other Region'),
    ]
    
    MOBILE_MONEY_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('vodafone', 'Vodafone Cash'),
        ('airteltigo', 'AirtelTigo Money'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone_number = models.CharField(max_length=20, verbose_name="Phone Number")
    date_of_birth = models.DateField(verbose_name="Date of Birth")
    
    # User relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Location and Payment
    region = models.CharField(max_length=20, choices=REGION_CHOICES, verbose_name="Region in Ghana")
    mobile_money_provider = models.CharField(max_length=20, choices=MOBILE_MONEY_CHOICES, verbose_name="Mobile Money Provider")
    
    # File Upload
    cv_file = models.FileField(
        upload_to='cv_files/',
        validators=[validate_cv_file],
        verbose_name="CV (PDF)"
    )
    
    # System Fields
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    terms_accepted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-registration_date']
        verbose_name = "Registration"
        verbose_name_plural = "Registrations"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # If user exists but registration doesn't have user linked, try to find by email
        if not self.user and self.email:
            try:
                user = User.objects.get(email=self.email)
                self.user = user
            except User.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f"/registration/{self.id}/"

class JobListing(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('basic_income', 'Basic Income'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    salary_range = models.CharField(max_length=100)
    requirements = models.TextField()
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return self.title

class MonthlyDraw(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    draw_month = models.DateField(unique=True)
    minimum_participants = models.IntegerField(default=5000)
    current_participants = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    winners_selected = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-draw_month']
    
    def __str__(self):
        return f"Draw for {self.draw_month.strftime('%B %Y')}"
    
    @property
    def is_ready_for_draw(self):
        return self.current_participants >= self.minimum_participants and self.status == 'active'

class Winner(models.Model):
    PRIZE_TYPE_CHOICES = [
        ('job', 'Job Position'),
        ('basic_income', 'Basic Income'),
    ]

    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    monthly_draw = models.ForeignKey(MonthlyDraw, on_delete=models.CASCADE)
    prize_type = models.CharField(max_length=20, choices=PRIZE_TYPE_CHOICES)
    prize_details = models.TextField()
    is_claimed = models.BooleanField(default=False)
    claim_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['registration', 'monthly_draw']

    def __str__(self):
        return f"{self.registration.full_name} - {self.prize_type}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('registration', 'Registration Fee'),
        ('monthly', 'Monthly Subscription'),
    ]

    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Paystack fields
    reference = models.CharField(max_length=100, unique=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    authorization_url = models.URLField(blank=True, null=True)
    access_code = models.CharField(max_length=100, blank=True, null=True)

    # Payment details
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    month_paid_for = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['registration', 'month_paid_for']),
        ]

    def __str__(self):
        return f"{self.registration.full_name} - GHS {self.amount} - {self.status}"

    @property
    def is_successful(self):
        return self.status == 'success'
