from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
import random

from registrations.models import MonthlyDraw, Registration, Winner, JobListing, Payment


class Command(BaseCommand):
    help = 'Select winners for monthly draw'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=str,
            help='Month to process (YYYY-MM format)',
        )
        parser.add_argument(
            '--job-winners',
            type=int,
            default=10,
            help='Number of job winners to select',
        )
        parser.add_argument(
            '--income-winners',
            type=int,
            default=5,
            help='Number of basic income winners to select',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes',
        )

    def handle(self, *args, **options):
        # Determine which month to process
        if options['month']:
            try:
                year, month = options['month'].split('-')
                draw_month = date(int(year), int(month), 1)
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid month format. Use YYYY-MM'))
                return
        else:
            draw_month = date.today().replace(day=1)

        self.stdout.write(f"Processing draw for {draw_month.strftime('%B %Y')}")

        # Get or create monthly draw
        try:
            monthly_draw = MonthlyDraw.objects.get(draw_month=draw_month)
        except MonthlyDraw.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No draw found for {draw_month.strftime("%B %Y")}'))
            return

        # Check if draw is ready
        if not monthly_draw.is_ready_for_draw:
            self.stdout.write(self.style.ERROR(
                f'Draw not ready. Current participants: {monthly_draw.current_participants}, '
                f'Minimum required: {monthly_draw.minimum_participants}'
            ))
            return

        # Check if winners already selected
        if monthly_draw.winners_selected:
            self.stdout.write(self.style.WARNING(f'Winners already selected for this draw'))
            return

        # Get eligible participants (those who paid for this month)
        eligible_registrations = Registration.objects.filter(
            is_active=True,
            payments__month_paid_for=draw_month,
            payments__status='success'
        ).distinct()

        eligible_count = eligible_registrations.count()
        self.stdout.write(f"Found {eligible_count} eligible participants")

        if eligible_count == 0:
            self.stdout.write(self.style.ERROR('No eligible participants found'))
            return

        # Get available jobs
        available_jobs = JobListing.objects.filter(is_active=True)
        job_count = available_jobs.count()

        # Adjust winner counts based on availability
        job_winners_count = min(options['job_winners'], job_count, eligible_count)
        income_winners_count = min(options['income_winners'], eligible_count - job_winners_count)

        self.stdout.write(f"Selecting {job_winners_count} job winners and {income_winners_count} income winners")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        # Convert to list for random selection
        participants_list = list(eligible_registrations)

        # Select job winners
        job_winners = []
        if job_winners_count > 0 and job_count > 0:
            selected_participants = random.sample(participants_list, job_winners_count)
            selected_jobs = list(available_jobs.order_by('?')[:job_winners_count])

            for i, registration in enumerate(selected_participants):
                job = selected_jobs[i % len(selected_jobs)]

                if not options['dry_run']:
                    winner = Winner.objects.create(
                        registration=registration,
                        monthly_draw=monthly_draw,
                        prize_type='job',
                        prize_details=f"{job.title} - {job.description[:200]}"
                    )
                    job_winners.append(winner)

                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Job Winner: {registration.full_name} - {job.title}"
                    ))

                    # Send notification email
                    self.send_winner_notification(registration, 'job', job.title)
                else:
                    self.stdout.write(f"[DRY RUN] Would select: {registration.full_name} for {job.title}")

                # Remove from participants list
                participants_list.remove(registration)

        # Select basic income winners
        income_winners = []
        if income_winners_count > 0 and len(participants_list) > 0:
            selected_participants = random.sample(participants_list, min(income_winners_count, len(participants_list)))

            for registration in selected_participants:
                if not options['dry_run']:
                    winner = Winner.objects.create(
                        registration=registration,
                        monthly_draw=monthly_draw,
                        prize_type='basic_income',
                        prize_details="1 Year Basic Income Support - GHS 500 per month for 12 months"
                    )
                    income_winners.append(winner)

                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Basic Income Winner: {registration.full_name}"
                    ))

                    # Send notification email
                    self.send_winner_notification(registration, 'basic_income', 'Basic Income')
                else:
                    self.stdout.write(f"[DRY RUN] Would select: {registration.full_name} for Basic Income")

        # Mark draw as completed
        if not options['dry_run']:
            monthly_draw.winners_selected = True
            monthly_draw.status = 'completed'
            monthly_draw.save()

            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Draw completed successfully!'
                f'\n  Total Job Winners: {len(job_winners)}'
                f'\n  Total Income Winners: {len(income_winners)}'
            ))
        else:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] Draw not marked as completed'))

    def send_winner_notification(self, registration, prize_type, prize_name):
        """Send email notification to winner"""
        try:
            subject = f"🎉 Congratulations! You've Won - Jobmarkt"

            if prize_type == 'job':
                message = f"""
Dear {registration.full_name},

Congratulations! You have been selected as a winner in this month's Jobmarkt draw!

🎉 YOU WON: {prize_name}

We will contact you within 48 hours with more details about your prize and next steps.

Please log in to your dashboard to view your winning details and claim your prize.

Dashboard: http://localhost:8000/user/dashboard/

Best regards,
The Jobmarkt Team
                """
            else:
                message = f"""
Dear {registration.full_name},

Congratulations! You have been selected as a winner in this month's Jobmarkt draw!

🎉 YOU WON: 1 Year Basic Income (GHS 500/month for 12 months)

We will contact you within 48 hours with more details about your prize and payment setup.

Please log in to your dashboard to view your winning details and claim your prize.

Dashboard: http://localhost:8000/user/dashboard/

Best regards,
The Jobmarkt Team
                """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [registration.email],
                fail_silently=True,
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to send email to {registration.email}: {str(e)}"))
