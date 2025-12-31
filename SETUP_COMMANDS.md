# Jobmarkt Setup Commands

## Complete Setup Guide

### 1. Install Dependencies (in virtual environment)

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install all required packages
pip install pypaystack2 requests

# Or install from pyproject.toml
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with your Paystack credentials:

```bash
# .env file
PAYSTACK_SECRET_KEY=sk_test_your_actual_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_actual_public_key_here
PAYSTACK_CALLBACK_URL=http://localhost:8000/payment/verify/

# Email Configuration (optional for now)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=noreply@jobmarkt.com
```

**Get Paystack Keys:**
- Sign up at https://dashboard.paystack.com
- Go to Settings > API Keys & Webhooks
- Copy your Test Secret Key (sk_test_...)
- Copy your Test Public Key (pk_test_...)

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow prompts to create admin credentials.

### 5. Run the Development Server

```bash
python manage.py runserver
```

Access the application at: http://localhost:8000

---

## How to Use the System

### For Testing Payments (Paystack Test Mode):

**Test Card Details:**
- Card Number: `5531886652142950`
- Expiry: Any future date (e.g., 12/25)
- CVV: `123`
- PIN: `3310`
- OTP: `123456`

### User Flow:
1. Go to http://localhost:8000
2. Click "Register Now"
3. Fill registration form and create account
4. Login to dashboard
5. Click "Pay Now - GHS 15" button
6. Complete payment with test card
7. You'll be redirected back after successful payment

### Admin Flow:
1. Go to http://localhost:8000/admin-dashboard/
2. Login with superuser credentials
3. View registrations, draws, payments, winners

### Select Winners (When Ready):

```bash
# Dry run to see who would be selected (no changes)
python manage.py select_winners --dry-run

# Actually select winners for current month
python manage.py select_winners --job-winners 10 --income-winners 5

# Select winners for specific month
python manage.py select_winners --month 2025-01 --job-winners 10 --income-winners 5
```

---

## Paystack Webhook Setup (For Production)

### 1. Set webhook URL in Paystack Dashboard:
- Go to Settings > API Keys & Webhooks
- Add webhook URL: `https://yourdomain.com/payment/webhook/`

### 2. Test webhook locally with ngrok:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Add to Paystack webhooks: https://abc123.ngrok.io/payment/webhook/
```

---

## Available URLs

### Public Pages:
- **Home**: http://localhost:8000/
- **How It Works**: http://localhost:8000/how-it-works/
- **FAQ**: http://localhost:8000/faq/

### User Pages:
- **Register**: http://localhost:8000/user/register/
- **Login**: http://localhost:8000/user/login/
- **Dashboard**: http://localhost:8000/user/dashboard/
- **Profile**: http://localhost:8000/user/profile/
- **Winners**: http://localhost:8000/user/winners/
- **Payment**: http://localhost:8000/payment/
- **Payment History**: http://localhost:8000/payment/history/

### Admin Pages (requires staff/superuser):
- **Admin Dashboard**: http://localhost:8000/admin-dashboard/
- **Registrations**: http://localhost:8000/admin-registrations/
- **Monthly Draws**: http://localhost:8000/admin-monthly-draws/
- **Winners**: http://localhost:8000/admin-winners/
- **Jobs**: http://localhost:8000/admin-jobs/

---

## Testing the Full Flow

### 1. Create Test Users:
```bash
# Create 10 test users with payments for current month
# (You'll need to create a management command for this, or do it manually)
```

### 2. Manual Testing Steps:
1. Register 5+ users through the website
2. Each user makes a payment (GHS 15)
3. Check admin dashboard - see participant count increase
4. When 5000+ participants (or manually adjust minimum in admin):
   - Go to admin panel
   - Create a MonthlyDraw with minimum_participants = 5 (for testing)
   - Set status to 'active'
5. Run: `python manage.py select_winners --dry-run`
6. Run: `python manage.py select_winners --job-winners 2 --income-winners 1`
7. Check winners in admin dashboard
8. Users can see their wins in their dashboard

---

## Database Models Created

1. **Registration** - User registration data with CV
2. **Payment** - Payment transactions (Paystack integration)
3. **MonthlyDraw** - Monthly lottery draws
4. **Winner** - Selected winners for each draw
5. **JobListing** - Available job positions

---

## Features Implemented

✅ User registration with CV upload
✅ User authentication (login/logout)
✅ Paystack payment integration
✅ Payment verification with webhooks
✅ User dashboard with stats
✅ Payment history tracking
✅ Admin dashboard
✅ Automatic winner selection algorithm
✅ Email notifications for winners
✅ Monthly draw management
✅ Winner claim tracking
✅ Job listings system
✅ Bilingual support (English/Dutch)

---

## Next Steps for Production

1. **Get Real Paystack Keys**
   - Sign up for Paystack business account
   - Submit required documents
   - Get live API keys (pk_live_... and sk_live_...)

2. **Configure Email**
   - Set up SMTP or use service like SendGrid, Mailgun
   - Update EMAIL_* settings in .env

3. **Deploy to Server**
   - Use platforms like Heroku, DigitalOcean, Railway
   - Set environment variables
   - Configure domain and SSL

4. **Set Up Cron Job**
   - Auto-run winner selection on 1st of each month
   - Send payment reminders

5. **Add More Features**
   - SMS notifications (using Twilio or Africa's Talking)
   - Employer portal for job posting
   - Advanced analytics
   - Multiple payment options

---

## Troubleshooting

### Payment not working?
- Check Paystack keys are correct
- Ensure you're using test keys with test cards
- Check webhook URL is accessible

### Winners not being selected?
- Ensure MonthlyDraw status is 'active'
- Check participant count >= minimum_participants
- Run with --dry-run first to debug

### Email not sending?
- Check EMAIL_* settings in .env
- For Gmail, use App Password not regular password
- For testing, check console backend or use mailtrap.io

---

## Support

For Paystack documentation: https://paystack.com/docs
For Django documentation: https://docs.djangoproject.com
