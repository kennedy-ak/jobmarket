from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Registration, MonthlyDraw, Winner, JobListing
import json

def is_staff_user(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """Custom admin dashboard"""
    
    # Get date ranges for filtering
    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Registration statistics
    total_registrations = Registration.objects.filter(is_active=True).count()
    this_month_registrations = Registration.objects.filter(
        registration_date__gte=this_month, 
        is_active=True
    ).count()
    last_month_registrations = Registration.objects.filter(
        registration_date__gte=last_month,
        registration_date__lt=this_month,
        is_active=True
    ).count()
    
    # Regional distribution
    regional_stats = Registration.objects.filter(is_active=True).values(
        'region'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Mobile money provider stats
    provider_stats = Registration.objects.filter(is_active=True).values(
        'mobile_money_provider'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent registrations
    recent_registrations = Registration.objects.filter(
        is_active=True
    ).order_by('-registration_date')[:10]
    
    # Monthly draw status
    current_draw = MonthlyDraw.objects.filter(
        draw_month=this_month
    ).first()
    
    # Recent winners
    recent_winners = Winner.objects.select_related(
        'registration', 'monthly_draw'
    ).order_by('-created_date')[:10]
    
    # Job listings
    active_jobs = JobListing.objects.filter(is_active=True).count()
    
    # Calculate progress percentage for current draw
    draw_progress = 0
    if current_draw and current_draw.minimum_participants > 0:
        draw_progress = (current_draw.current_participants / current_draw.minimum_participants) * 100
    
    context = {
        'total_registrations': total_registrations,
        'this_month_registrations': this_month_registrations,
        'last_month_registrations': last_month_registrations,
        'registration_growth': ((this_month_registrations - last_month_registrations) / max(last_month_registrations, 1)) * 100,
        'regional_stats': regional_stats,
        'provider_stats': provider_stats,
        'recent_registrations': recent_registrations,
        'current_draw': current_draw,
        'recent_winners': recent_winners,
        'active_jobs': active_jobs,
        'draw_progress': draw_progress,
        'page_title': 'Admin Dashboard',
    }
    
    return render(request, 'registrations/admin_simple.html', context)

@login_required
@user_passes_test(is_staff_user)
def admin_registrations(request):
    """Admin registrations management page"""
    
    registrations = Registration.objects.select_related().order_by('-registration_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        registrations = registrations.filter(
            first_name__icontains=search_query) | registrations.filter(
            last_name__icontains=search_query) | registrations.filter(
            email__icontains=search_query)
    
    # Filter by region
    region_filter = request.GET.get('region', '')
    if region_filter:
        registrations = registrations.filter(region=region_filter)
    
    # Filter by provider
    provider_filter = request.GET.get('provider', '')
    if provider_filter:
        registrations = registrations.filter(mobile_money_provider=provider_filter)
    
    context = {
        'registrations': registrations,
        'search_query': search_query,
        'region_filter': region_filter,
        'provider_filter': provider_filter,
        'page_title': 'Manage Registrations',
    }
    
    return render(request, 'registrations/admin_registrations.html', context)

@login_required
@user_passes_test(is_staff_user)
def admin_monthly_draws(request):
    """Admin monthly draws management page"""
    
    draws = MonthlyDraw.objects.order_by('-draw_month')
    
    context = {
        'draws': draws,
        'page_title': 'Monthly Draws',
    }
    
    return render(request, 'registrations/admin_monthly_draws.html', context)

@login_required
@user_passes_test(is_staff_user)
def admin_winners(request):
    """Admin winners management page"""
    
    winners = Winner.objects.select_related(
        'registration', 'monthly_draw'
    ).order_by('-created_date')
    
    context = {
        'winners': winners,
        'page_title': 'Winners',
    }
    
    return render(request, 'registrations/admin_winners.html', context)

@login_required
@user_passes_test(is_staff_user)
def admin_jobs(request):
    """Admin job listings management page"""
    
    jobs = JobListing.objects.order_by('-created_date')
    
    context = {
        'jobs': jobs,
        'page_title': 'Job Listings',
    }
    
    return render(request, 'registrations/admin_jobs.html', context)

@login_required
@user_passes_test(is_staff_user)
def admin_registration_detail(request, registration_id):
    """Detailed view of a registration"""
    
    registration = get_object_or_404(Registration, id=registration_id)
    
    context = {
        'registration': registration,
        'page_title': f'Registration Detail - {registration.full_name}',
    }
    
    return render(request, 'registrations/admin_registration_detail.html', context)