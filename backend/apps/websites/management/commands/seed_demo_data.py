from django.core.management.base import BaseCommand
from apps.domains.models import Domain
from apps.cards.models import BusinessCard
from apps.websites.models import Industry, Website


class Command(BaseCommand):
    help = "Seeds initial demo data for business card and website"

    def handle(self, *args, **options):
        # 1. Demo Business Card
        card_domain, _ = Domain.objects.get_or_create(
            domain_name='sarahconsulting.com',
            defaults={'domain_type': 'custom', 'verification_status': 'verified', 'ssl_status': 'active'}
        )
        card, created = BusinessCard.objects.get_or_create(
            slug='apex-consulting-studio',
            defaults={
                'domain': card_domain,
                'business_name': 'Apex Consulting Studio',
                'owner_name': 'Sarah Jenkins',
                'tagline': 'Corporate Strategy & Growth Advisory',
                'description': 'Empowering emerging companies and founders with venture readiness and operating models.',
                'services': 'M&A Advisory, Growth Strategy, Venture Capital Structuring, Operational Scaling',
                'phone': '+1 (555) 234-5678',
                'email': 'sarah@apexconsulting.com',
                'whatsapp': '+15552345678',
                'address': '450 Lexington Ave, New York, NY 10017',
                'google_maps_url': 'https://maps.google.com',
                'existing_website': 'https://apexconsulting.com',
                'theme_color': '#2563EB',
                'social_links': {
                    'linkedin': 'https://linkedin.com',
                    'twitter': 'https://twitter.com'
                },
                'is_published': True
            }
        )

        # 2. Demo Website
        tech_ind = Industry.objects.filter(slug='technology-and-it').first()
        site_domain, _ = Domain.objects.get_or_create(
            domain_name='novastack.io',
            defaults={'domain_type': 'custom', 'verification_status': 'verified', 'ssl_status': 'active'}
        )
        site, created_site = Website.objects.get_or_create(
            slug='novastack-systems',
            defaults={
                'domain': site_domain,
                'industry': tech_ind,
                'title': 'NovaStack AI Systems',
                'tagline': 'Next-Generation Autonomous Cloud Solutions',
                'about_text': 'NovaStack is a premier enterprise software and AI infrastructure firm. We engineer resilient distributed systems, custom LLM pipelines, and automated cloud workflows.',
                'primary_color': '#1E40AF',
                'secondary_color': '#0EA5E9',
                'contact_email': 'contact@novastack.io',
                'contact_phone': '+1 (800) 555-NOVA',
                'address': '100 Silicon Blvd, Suite 500, Austin, TX',
                'working_hours': 'Mon - Fri: 8:00 AM - 6:00 PM CST',
                'custom_data': {
                    'services_list': 'Autonomous AI Agents • Distributed Cloud Architecture • High-Throughput APIs',
                    'tech_stack': 'Python, PyTorch, Kubernetes, Go, AWS, Docker',
                    'featured_projects': 'Enterprise Agent Mesh (serving 2M requests/day), FinTech Real-time Risk Engine',
                    'client_count': '120+ Global Enterprise Deployments'
                },
                'status': 'published',
                'is_published': True
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo card and website!'))

