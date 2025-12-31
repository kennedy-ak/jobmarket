from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
import json
import os
from .models import Registration, MonthlyDraw, Winner
from .forms import RegistrationForm, LanguageForm

def home(request):
    """Main landing page view"""
    # Get current language from session or default to English
    language = request.session.get('language', 'en')
    
    # Get the current or next monthly draw
    from datetime import datetime, date
    today = date.today()
    current_month = today.replace(day=1)
    
    try:
        monthly_draw = MonthlyDraw.objects.get(draw_month=current_month)
    except MonthlyDraw.DoesNotExist:
        # Create new monthly draw for current month
        monthly_draw = MonthlyDraw.objects.create(
            draw_month=current_month,
            status='active' if Registration.objects.count() >= 5000 else 'pending'
        )
    
    context = {
        'language': language,
        'monthly_draw': monthly_draw,
        'total_participants': Registration.objects.filter(is_active=True).count(),
        'needed_participants': max(0, monthly_draw.minimum_participants - Registration.objects.filter(is_active=True).count()),
    }
    
    return render(request, 'registrations/home.html', context)

def registration_view(request):
    """Registration form view"""
    language = request.session.get('language', 'en')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES, language=language)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.language = language
            registration.terms_accepted = True
            registration.save()
            
            # Update monthly draw participant count
            from datetime import date
            current_month = date.today().replace(day=1)
            try:
                monthly_draw = MonthlyDraw.objects.get(draw_month=current_month)
                monthly_draw.current_participants += 1
                monthly_draw.save()
            except MonthlyDraw.DoesNotExist:
                pass
            
            # Handle success response based on language
            if language == 'en':
                messages.success(request, 'Thank you for your registration! You will now be redirected to the Mobile Money payment page.')
            else:
                messages.success(request, 'Bedankt voor je registratie! Je wordt nu doorgestuurd naar de Mobiel Geld betalingspagina.')
            
            return redirect('registration_success')
    else:
        form = RegistrationForm(language=language)
    
    context = {
        'form': form,
        'language': language,
    }
    
    return render(request, 'registrations/registration.html', context)

def registration_success(request):
    """Registration success page"""
    language = request.session.get('language', 'en')
    
    context = {
        'language': language,
    }
    
    return render(request, 'registrations/registration_success.html', context)

def set_language(request):
    """Set user language preference"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            language = data.get('language', 'en')
            
            # Validate language
            if language not in ['en', 'nl']:
                language = 'en'
            
            # Store in session
            request.session['language'] = language
            
            return JsonResponse({
                'status': 'success',
                'language': language,
                'message': 'Language updated successfully'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

@require_http_methods(["GET"])
def get_language(request):
    """Get current language preference"""
    language = request.session.get('language', 'en')
    return JsonResponse({'language': language})

def faq_view(request):
    """FAQ page view"""
    language = request.session.get('language', 'en')
    
    # FAQ data - could be from database in future
    faqs = [
        {
            'question_en': 'What are my chances of getting a job or basic income?',
            'question_nl': 'Hoe groot is mijn kans op een baan of basisinkomen?',
            'answer_en': 'Your chance depends on the number of participants. With the minimum of 5,000 participants, your chance is 1 in 5,000 per month. The more participants, the more jobs and basic incomes we can offer.',
            'answer_nl': 'Je kans is afhankelijk van het aantal deelnemers. Bij het minimum van 5.000 deelnemers is je kans 1 op 5.000 per maand. Hoe meer deelnemers, hoe meer banen en basisinkomens we kunnen aanbieden.'
        },
        {
            'question_en': 'What exactly does the basic income include?',
            'question_nl': 'Wat houdt het basisinkomen precies in?',
            'answer_en': 'The basic income is a monthly payment of GHS 1,500-2,000 (depending on your experience and education) that you receive for 12 months, regardless of whether you find work during that period.',
            'answer_nl': 'Het basisinkomen is een maandelijkse uitkering van GHS 1.500-2.000 (afhankelijk van je ervaring en opleiding) die je gedurende 12 maanden ontvangt, ongeacht of je in die periode werk vindt.'
        },
        {
            'question_en': 'Can I unsubscribe at any time?',
            'question_nl': 'Kan ik me op elk moment uitschrijven?',
            'answer_en': 'Yes, you can unsubscribe at any time. The monthly payment will then stop at the end of the current billing period.',
            'answer_nl': 'Ja, je kunt je op elk moment uitschrijven. De maandelijkse betaling stopt dan aan het einde van de huidige factureringsperiode.'
        },
        {
            'question_en': 'How are winners selected?',
            'question_nl': 'Hoe worden winnaars geselecteerd?',
            'answer_en': 'We use a transparent, random selection system that is verified by an independent party. All participants have equal chances.',
            'answer_nl': 'We gebruiken een transparant, willekeurig selectiesysteem dat wordt gecontroleerd door een onafhankelijke partij. Alle deelnemers hebben gelijke kansen.'
        },
        {
            'question_en': 'What happens if there are fewer than 5,000 participants?',
            'question_nl': 'Wat gebeurt er als er minder dan 5.000 deelnemers zijn?',
            'answer_en': 'With fewer than 5,000 participants, the monthly draw is postponed until the minimum number of participants is reached. You only pay when the draw takes place.',
            'answer_nl': 'Bij minder dan 5.000 deelnemers wordt de maandelijkse trekking uitgesteld totdat het minimum aantal deelnemers is bereikt. Je betaalt pas wanneer de trekking plaatsvindt.'
        }
    ]
    
    context = {
        'language': language,
        'faqs': faqs,
    }
    
    return render(request, 'registrations/faq.html', context)

def how_it_works_view(request):
    """How it works page view"""
    language = request.session.get('language', 'en')
    
    context = {
        'language': language,
    }
    
    return render(request, 'registrations/how_it_works.html', context)
