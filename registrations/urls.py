from django.urls import path
from . import views
from . import admin_views
from . import user_views
from . import payment_views

urlpatterns = [
    path('', views.home, name='home'),
    path('registration/', views.registration_view, name='registration'),
    path('registration/success/', views.registration_success, name='registration_success'),
    path('faq/', views.faq_view, name='faq'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('api/set-language/', views.set_language, name='set_language'),
    path('api/get-language/', views.get_language, name='get_language'),

    # User authentication routes
    path('user/register/', user_views.user_register, name='user_register'),
    path('user/login/', user_views.user_login, name='user_login'),
    path('user/logout/', user_views.user_logout, name='user_logout'),
    path('user/dashboard/', user_views.user_dashboard, name='user_dashboard'),
    path('user/profile/', user_views.user_profile, name='user_profile'),
    path('user/winners/', user_views.user_winners, name='user_winners'),

    # Payment routes
    path('payment/', payment_views.initiate_payment, name='payment_page'),
    path('payment/verify/', payment_views.verify_payment, name='verify_payment'),
    path('payment/webhook/', payment_views.paystack_webhook, name='paystack_webhook'),
    path('payment/history/', payment_views.payment_history, name='payment_history'),

    # Admin dashboard routes
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-registrations/', admin_views.admin_registrations, name='admin_registrations'),
    path('admin-monthly-draws/', admin_views.admin_monthly_draws, name='admin_monthly_draws'),
    path('admin-winners/', admin_views.admin_winners, name='admin_winners'),
    path('admin-jobs/', admin_views.admin_jobs, name='admin_jobs'),
    path('admin-registration/<int:registration_id>/', admin_views.admin_registration_detail, name='admin_registration_detail'),
]