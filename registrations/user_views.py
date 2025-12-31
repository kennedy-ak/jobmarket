from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Registration, MonthlyDraw, Winner
from .forms import RegistrationForm, UserLoginForm, UserRegistrationForm
from datetime import datetime, date

def user_register(request):
    """User registration with account creation"""
    language = request.session.get('language', 'en')
    
    if request.method == 'POST':
        # Handle both Django user creation and registration data
        user_form = UserRegistrationForm(request.POST)
        registration_form = RegistrationForm(request.POST, request.FILES, language=language)
        
        if user_form.is_valid() and registration_form.is_valid():
            # Create Django user
            user = user_form.save()
            
            # Create registration linked to user
            registration = registration_form.save(commit=False)
            registration.user = user
            registration.language = language
            registration.terms_accepted = True
            registration.save()
            
            # Log the user in
            login(request, user)
            
            # Update monthly draw participant count
            current_month = date.today().replace(day=1)
            try:
                monthly_draw = MonthlyDraw.objects.get(draw_month=current_month)
                monthly_draw.current_participants += 1
                monthly_draw.save()
            except MonthlyDraw.DoesNotExist:
                pass
            
            return redirect('user_dashboard')
    else:
        user_form = UserRegistrationForm()
        registration_form = RegistrationForm(language=language)
    
    context = {
        'user_form': user_form,
        'registration_form': registration_form,
        'language': language,
    }
    
    return render(request, 'registrations/user_register.html', context)

def user_login(request):
    """User login view"""
    language = request.session.get('language', 'en')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('user_dashboard')
            else:
                if language == 'en':
                    messages.error(request, 'Invalid username or password.')
                else:
                    messages.error(request, 'Ongeldige gebruikersnaam of wachtwoord.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'language': language,
    }
    
    return render(request, 'registrations/user_login.html', context)

def user_logout(request):
    """User logout view"""
    logout(request)
    return redirect('home')

@login_required
def user_dashboard(request):
    """User personal dashboard"""
    language = request.session.get('language', 'en')
    
    try:
        # Get user's registration
        registration = Registration.objects.get(user=request.user)
        
        # Get current monthly draw
        current_month = date.today().replace(day=1)
        try:
            monthly_draw = MonthlyDraw.objects.get(draw_month=current_month)
        except MonthlyDraw.DoesNotExist:
            monthly_draw = MonthlyDraw.objects.create(
                draw_month=current_month,
                status='active' if Registration.objects.count() >= 5000 else 'pending'
            )
        
        # Get user's winner history
        user_winners = Winner.objects.filter(registration=registration).order_by('-created_date')
        
        # Calculate user's chances
        total_participants = Registration.objects.filter(is_active=True).count()
        user_chances = f"1 in {total_participants}" if total_participants > 0 else "0"
        
        # Registration statistics
        registration_date = registration.registration_date
        
        context = {
            'registration': registration,
            'monthly_draw': monthly_draw,
            'user_winners': user_winners,
            'user_chances': user_chances,
            'total_participants': total_participants,
            'registration_date': registration_date,
            'language': language,
        }
        
        return render(request, 'registrations/user_dashboard.html', context)
        
    except Registration.DoesNotExist:
        # User exists but no registration record
        messages.warning(request, 'Registration record not found. Please contact support.')
        return redirect('home')

@login_required
def user_profile(request):
    """User profile management"""
    language = request.session.get('language', 'en')

    try:
        registration = Registration.objects.get(user=request.user)

        if request.method == 'POST':
            # Handle profile updates for allowed fields
            phone_number = request.POST.get('phone_number')
            region = request.POST.get('region')
            mobile_money_provider = request.POST.get('mobile_money_provider')

            # Update allowed fields
            if phone_number:
                registration.phone_number = phone_number
            if region:
                registration.region = region
            if mobile_money_provider:
                registration.mobile_money_provider = mobile_money_provider

            # Handle CV upload if provided
            if 'cv_file' in request.FILES:
                registration.cv_file = request.FILES['cv_file']

            registration.save()

            if language == 'en':
                messages.success(request, 'Profile updated successfully!')
            else:
                messages.success(request, 'Profiel succesvol bijgewerkt!')

            return redirect('user_profile')
        else:
            context = {
                'registration': registration,
                'language': language,
            }
            return render(request, 'registrations/user_profile.html', context)

    except Registration.DoesNotExist:
        messages.error(request, 'Registration record not found.')
        return redirect('user_dashboard')

@login_required
def user_winners(request):
    """User winners history"""
    language = request.session.get('language', 'en')
    
    try:
        registration = Registration.objects.get(user=request.user)
        user_winners = Winner.objects.filter(registration=registration).order_by('-created_date')
        
        context = {
            'user_winners': user_winners,
            'language': language,
        }
        
        return render(request, 'registrations/user_winners.html', context)
        
    except Registration.DoesNotExist:
        messages.error(request, 'Registration record not found.')
        return redirect('user_dashboard')