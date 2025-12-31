from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date, datetime
import uuid
import hashlib
import hmac
import json

from pypaystack2.sub_clients import TransactionClient
from .models import Payment, Registration, MonthlyDraw


def generate_reference():
    """Generate unique payment reference"""
    return f"JM-{uuid.uuid4().hex[:12].upper()}"


@login_required
def initiate_payment(request):
    """Initialize Paystack payment"""
    language = request.session.get('language', 'en')

    try:
        registration = Registration.objects.get(user=request.user)
    except Registration.DoesNotExist:
        messages.error(request, 'Registration record not found. Please complete registration first.')
        return redirect('user_register')

    if request.method == 'POST':
        payment_type = request.POST.get('payment_type', 'monthly')

        # Get current month
        current_month = date.today().replace(day=1)

        # Check if user already paid for this month
        existing_payment = Payment.objects.filter(
            registration=registration,
            month_paid_for=current_month,
            status='success'
        ).first()

        if existing_payment:
            if language == 'en':
                messages.warning(request, 'You have already paid for this month!')
            else:
                messages.warning(request, 'Je hebt al betaald voor deze maand!')
            return redirect('user_dashboard')

        # Create payment record
        reference = generate_reference()
        amount = settings.MONTHLY_SUBSCRIPTION_AMOUNT  # Amount in pesewas

        payment = Payment.objects.create(
            registration=registration,
            user=request.user,
            amount=amount / 100,  # Convert to GHS for storage
            payment_type=payment_type,
            reference=reference,
            email=registration.email,
            phone_number=registration.phone_number,
            month_paid_for=current_month
        )

        try:
            # Initialize Paystack transaction
            transaction = TransactionClient(secret_key=settings.PAYSTACK_SECRET_KEY)

            response = transaction.initialize(
                email=registration.email,
                amount=amount,  # Amount in pesewas
                reference=reference,
                callback_url=settings.PAYSTACK_CALLBACK_URL,
                metadata={
                    'payment_id': payment.id,
                    'user_id': request.user.id,
                    'registration_id': registration.id,
                    'month': current_month.strftime('%Y-%m')
                }
            )

            if response['status']:
                # Update payment with Paystack details
                payment.authorization_url = response['data']['authorization_url']
                payment.access_code = response['data']['access_code']
                payment.paystack_reference = response['data']['reference']
                payment.save()

                # Redirect to Paystack payment page
                return redirect(response['data']['authorization_url'])
            else:
                payment.status = 'failed'
                payment.save()
                messages.error(request, 'Failed to initialize payment. Please try again.')
                return redirect('payment_page')

        except Exception as e:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment initialization error: {str(e)}')
            return redirect('payment_page')

    # GET request - show payment page
    context = {
        'registration': registration,
        'amount': settings.MONTHLY_SUBSCRIPTION_AMOUNT / 100,
        'language': language,
    }
    return render(request, 'registrations/payment.html', context)


@csrf_exempt
def verify_payment(request):
    """Verify Paystack payment callback"""
    if request.method == 'GET':
        reference = request.GET.get('reference')

        if not reference:
            messages.error(request, 'Invalid payment reference.')
            return redirect('payment_page')

        try:
            payment = Payment.objects.get(reference=reference)
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found.')
            return redirect('payment_page')

        # Verify with Paystack
        try:
            transaction = TransactionClient(secret_key=settings.PAYSTACK_SECRET_KEY)
            response = transaction.verify(reference=reference)

            if response['status'] and response['data']['status'] == 'success':
                # Payment successful
                payment.status = 'success'
                payment.paid_at = timezone.now()
                payment.payment_method = response['data']['channel']
                payment.paystack_reference = response['data']['reference']
                payment.save()

                # Update monthly draw participant count
                current_month = payment.month_paid_for
                monthly_draw, created = MonthlyDraw.objects.get_or_create(
                    draw_month=current_month,
                    defaults={
                        'minimum_participants': 5000,
                        'current_participants': 0,
                        'status': 'pending'
                    }
                )

                # Increment participant count
                monthly_draw.current_participants += 1

                # Check if threshold reached
                if monthly_draw.current_participants >= monthly_draw.minimum_participants and monthly_draw.status == 'pending':
                    monthly_draw.status = 'active'

                monthly_draw.save()

                language = request.session.get('language', 'en')
                if language == 'en':
                    messages.success(request, f'Payment successful! You are now entered in the {current_month.strftime("%B %Y")} draw.')
                else:
                    messages.success(request, f'Betaling succesvol! Je bent nu ingeschreven voor de trekking van {current_month.strftime("%B %Y")}.')

                return redirect('user_dashboard')
            else:
                # Payment failed
                payment.status = 'failed'
                payment.save()
                messages.error(request, 'Payment verification failed. Please contact support.')
                return redirect('payment_page')

        except Exception as e:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment verification error: {str(e)}')
            return redirect('payment_page')

    return HttpResponse('Invalid request method', status=405)


@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook events"""
    if request.method == 'POST':
        # Verify webhook signature
        signature = request.headers.get('X-Paystack-Signature')

        if not signature:
            return HttpResponse('No signature', status=400)

        # Compute hash
        hash_value = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            request.body,
            hashlib.sha512
        ).hexdigest()

        if hash_value != signature:
            return HttpResponse('Invalid signature', status=400)

        # Process webhook
        try:
            data = json.loads(request.body)
            event = data.get('event')

            if event == 'charge.success':
                reference = data['data']['reference']

                try:
                    payment = Payment.objects.get(reference=reference)

                    if payment.status != 'success':
                        payment.status = 'success'
                        payment.paid_at = timezone.now()
                        payment.payment_method = data['data']['channel']
                        payment.save()

                        # Update monthly draw
                        current_month = payment.month_paid_for
                        monthly_draw, created = MonthlyDraw.objects.get_or_create(
                            draw_month=current_month,
                            defaults={
                                'minimum_participants': 5000,
                                'current_participants': 0,
                                'status': 'pending'
                            }
                        )

                        monthly_draw.current_participants += 1

                        if monthly_draw.current_participants >= monthly_draw.minimum_participants and monthly_draw.status == 'pending':
                            monthly_draw.status = 'active'

                        monthly_draw.save()

                except Payment.DoesNotExist:
                    pass

            return HttpResponse('Webhook processed', status=200)

        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)

    return HttpResponse('Invalid request method', status=405)


@login_required
def payment_history(request):
    """View user's payment history"""
    language = request.session.get('language', 'en')

    try:
        registration = Registration.objects.get(user=request.user)
        payments = Payment.objects.filter(registration=registration).order_by('-created_date')

        context = {
            'registration': registration,
            'payments': payments,
            'language': language,
        }

        return render(request, 'registrations/payment_history.html', context)

    except Registration.DoesNotExist:
        messages.error(request, 'Registration record not found.')
        return redirect('user_dashboard')
