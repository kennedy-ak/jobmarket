from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from .models import Registration
import os

class RegistrationForm(forms.ModelForm):
    confirm_terms = forms.BooleanField(
        required=True,
        label="I agree to the terms and conditions and privacy policy",
        widget=forms.CheckboxInput(attrs={
            'id': 'voorwaarden',
            'required': True
        })
    )
    
    class Meta:
        model = Registration
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'region', 'cv_file', 'mobile_money_provider'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'voornaam',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'achternaam',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'email',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'telefoon',
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'id': 'geboortedatum',
                'type': 'date',
                'required': True
            }),
            'region': forms.Select(attrs={
                'class': 'form-control',
                'id': 'location',
                'required': True
            }),
            'cv_file': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'cv',
                'accept': '.pdf',
                'required': True
            }),
            'mobile_money_provider': forms.Select(attrs={
                'class': 'form-control',
                'id': 'mobile-money',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', 'en')
        super().__init__(*args, **kwargs)
        
        # Set language-specific labels
        if language == 'nl':
            self.fields['first_name'].label = "Voornaam"
            self.fields['last_name'].label = "Achternaam"
            self.fields['email'].label = "E-mailadres"
            self.fields['phone_number'].label = "Telefoonnummer"
            self.fields['date_of_birth'].label = "Geboortedatum"
            self.fields['region'].label = "Locatie in Ghana"
            self.fields['cv_file'].label = "Upload CV (PDF, max 5MB)"
            self.fields['mobile_money_provider'].label = "Mobiel Geld Provider"
            self.fields['confirm_terms'].label = "Ik ga akkoord met de algemene voorwaarden en het privacybeleid"
        
        # Set placeholder for region select
        if language == 'en':
            self.fields['region'].empty_label = "Select your region"
            self.fields['mobile_money_provider'].empty_label = "Select your provider"
        else:
            self.fields['region'].empty_label = "Selecteer je regio"
            self.fields['mobile_money_provider'].empty_label = "Selecteer je provider"
    
    def clean_cv_file(self):
        cv_file = self.cleaned_data.get('cv_file')
        
        if cv_file:
            # Check file size (5MB max)
            if cv_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size should not exceed 5MB.")
            
            # Check file extension
            valid_extensions = ['.pdf']
            ext = os.path.splitext(cv_file.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError("Only PDF files are allowed.")
        
        return cv_file
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Registration.objects.filter(email=email).exists():
            raise forms.ValidationError("A registration with this email already exists.")
        return email

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', 'en')
        super().__init__(*args, **kwargs)
        
        # Style the fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Password' if language == 'en' else 'Wachtwoord'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Confirm Password' if language == 'en' else 'Bevestig Wachtwoord'

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        language = kwargs.pop('language', 'en')
        super().__init__(*args, **kwargs)
        
        # Style the fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class LanguageForm(forms.Form):
    LANGUAGE_CHOICES = [
        ('en', 'EN'),
        ('nl', 'NL'),
    ]
    
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.HiddenInput(),
        initial='en'
    )