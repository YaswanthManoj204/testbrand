from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.domains.models import Domain
from apps.cards.models import BusinessCard
from apps.websites.models import Industry, Website, ContactSubmission


class BrandNestAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.industry = Industry.objects.create(
            name="Technology and IT",
            slug="technology-and-it",
            icon="bi-cpu",
            form_schema={"sections": []}
        )

    def test_health_check(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_domain_connect_and_verification(self):
        # 1. Connect domain
        connect_data = {
            'domain_name': 'acme-corp.com',
            'domain_type': 'custom'
        }
        response = self.client.post('/api/v1/domains/connect/', connect_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        domain_id = response.data['domain']['id']
        self.assertTrue('brandnest-verify-' in response.data['domain']['verification_token'])
        self.assertIn('dns_instructions', response.data)

        # 2. Verify domain
        verify_response = self.client.post(f'/api/v1/domains/{domain_id}/verify/')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(verify_response.data['domain']['verification_status'], 'verified')
        self.assertEqual(verify_response.data['domain']['ssl_status'], 'active')

    def test_business_card_creation_and_public_api(self):
        domain = Domain.objects.create(
            domain_name='johnsmith.me',
            verification_status='verified'
        )
        card_data = {
            'business_name': 'Apex Legal Studio',
            'owner_name': 'John Smith',
            'tagline': 'Corporate Law & Counsel',
            'phone': '+1 (555) 234-5678',
            'email': 'john@apexlegal.com',
            'domain': domain.id,
            'is_published': True
        }
        create_res = self.client.post('/api/v1/cards/', card_data, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        card_id = create_res.data['card_id']

        # Access public card via card_id
        pub_res = self.client.get(f'/api/v1/cards/public/{card_id}/')
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pub_res.data['business_name'], 'Apex Legal Studio')
        self.assertEqual(pub_res.data['domain_name'], 'johnsmith.me')

    def test_website_creation_and_public_api(self):
        domain = Domain.objects.create(
            domain_name='novastack.io',
            verification_status='verified'
        )
        site_data = {
            'title': 'NovaStack AI Systems',
            'tagline': 'Enterprise AI Solutions',
            'industry': self.industry.id,
            'domain': domain.id,
            'contact_email': 'contact@novastack.io',
            'custom_data': {
                'services_list': 'AI Agents, Model Fine-tuning',
                'tech_stack': 'Python, PyTorch, Kubernetes'
            },
            'is_published': True,
            'status': 'published'
        }
        create_res = self.client.post('/api/v1/websites/', site_data, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        site_id = create_res.data['site_id']

        # Access public website via site_id
        pub_res = self.client.get(f'/api/v1/websites/public/{site_id}/')
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pub_res.data['title'], 'NovaStack AI Systems')
        self.assertEqual(pub_res.data['industry_name'], 'Technology and IT')

        # Test visitor contact enquiry submission
        enquiry_res = self.client.post(
            f'/api/v1/websites/{create_res.data["id"]}/enquiries/',
            {
                'visitor_name': 'Alice Wonder',
                'visitor_email': 'alice@example.com',
                'message': 'We would love a consultation.'
            },
            format='json'
        )
        self.assertEqual(enquiry_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactSubmission.objects.filter(website__site_id=site_id).count(), 1)
