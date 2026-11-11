from django.test import TestCase, Client
from django.urls import reverse
from apps.domains.models import Domain
from apps.cards.models import BusinessCard
from apps.websites.models import Industry, Website


class FrontendFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.industry = Industry.objects.create(
            name="Technology and IT",
            slug="technology-and-it",
            icon="bi-cpu",
            form_schema={
                "sections": [
                    {
                        "id": "services",
                        "title": "Services",
                        "fields": [{"name": "services_list", "label": "Services", "type": "text"}]
                    }
                ]
            }
        )

    def test_landing_page(self):
        res = self.client.get(reverse('landing'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Build business card")
        self.assertContains(res, "Make your website")

    def test_card_builder_get(self):
        res = self.client.get(reverse('card_builder'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Build your digital business card")
        self.assertContains(res, "Existing website")

    def test_card_builder_post_flow(self):
        post_data = {
            'business_name': 'Sarah Legal & Advisory',
            'owner_name': 'Sarah Jenkins',
            'tagline': 'Corporate Law Partner',
            'phone': '+1 555 123 4567',
            'email': 'sarah@legal.com',
            'whatsapp': '+15551234567',
            'address': '450 Lexington Ave, NY',
            'existing_website': 'https://sarahconsulting.com',
            'theme_color': '#2563EB',
            'social_linkedin': 'https://linkedin.com/in/sarahjenkins',
        }
        res = self.client.post(reverse('card_builder'), post_data)
        self.assertEqual(res.status_code, 302)  # Redirects to preview

        card = BusinessCard.objects.get(business_name='Sarah Legal & Advisory')
        self.assertEqual(card.existing_website, 'https://sarahconsulting.com')

        # Test card preview page
        preview_res = self.client.get(reverse('card_preview', kwargs={'card_id': card.card_id}))
        self.assertEqual(preview_res.status_code, 200)
        self.assertContains(preview_res, 'Sarah Legal &amp; Advisory')
        self.assertContains(preview_res, 'sarahconsulting.com')
        self.assertContains(preview_res, 'sarahconsulting.com')

        # Test standalone card template
        standalone_res = self.client.get(reverse('card_standalone', kwargs={'slug': card.slug}))
        self.assertEqual(standalone_res.status_code, 200)
        self.assertContains(standalone_res, 'Sarah Legal &amp; Advisory')

    def test_card_builder_with_custom_layout_order(self):
        post_data = {
            'business_name': 'Medowa Global Pvt Ltd',
            'owner_name': 'Sujithra Ramaswamy',
            'role_title': 'Head-Business & Operations',
            'banner_tagline': 'We Solve Business Challenges',
            'about_heading': 'ELEVATE YOUR DIGITAL PRESENCE.',
            'bio': 'Strategic digital marketing partners.',
            'services': 'Search Engine Optimization, Search Engine Marketing',
            'brands': 'Qklly Connect, BlackPillar',
            'phone': '+91 98765 43210',
            'email': 'sujithra@medowaglobal.com',
            'whatsapp': '+919876543210',
            'address': 'Chennai, Tamil Nadu, India',
            'website': 'medowaglobal.com',
            'accent_color': '#0084FF',
            'linkedin': 'https://linkedin.com/in/sujithra',
            'youtube': 'https://youtube.com/@medowaglobal',
            'section_order': '["about", "capabilities", "connect", "callback", "brands", "socials"]',
            'disabled_sections': '[]'
        }
        res = self.client.post(reverse('card_builder'), post_data)
        self.assertEqual(res.status_code, 302)

        card = BusinessCard.objects.get(business_name='Medowa Global Pvt Ltd')
        self.assertEqual(card.owner_name, 'Sujithra Ramaswamy')
        self.assertEqual(card.layout_config['role_title'], 'Head-Business & Operations')
        self.assertEqual(card.layout_config['section_order'], ['about', 'capabilities', 'connect', 'callback', 'brands', 'socials'])

        # Standalone verification
        res_view = self.client.get(reverse('card_standalone', kwargs={'slug': card.slug}))
        self.assertEqual(res_view.status_code, 200)
        self.assertContains(res_view, 'ELEVATE YOUR DIGITAL PRESENCE.')
        self.assertContains(res_view, 'Sujithra Ramaswamy')

    def test_website_builder_get(self):
        res = self.client.get(reverse('website_builder'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Choose Your Industry")
        self.assertContains(res, "Technology and IT")

    def test_website_builder_post_flow(self):
        post_data = {
            'domain_name': 'hypercloud.io',
            'industry_slug': 'technology-and-it',
            'title': 'HyperCloud Infrastructure',
            'tagline': 'Next-Gen Serverless Hosting',
            'about_text': 'Building automated cloud deployments.',
            'contact_email': 'ops@hypercloud.io',
            'contact_phone': '+1 800 555 9999',
            'address': '100 Tech Blvd, Austin TX',
            'custom_services_list': 'Multi-cloud Kubernetes, Edge CI/CD',
        }
        res = self.client.post(reverse('website_builder'), post_data)
        self.assertEqual(res.status_code, 302)  # Redirects to preview

        site = Website.objects.get(title='HyperCloud Infrastructure')
        self.assertEqual(site.domain.domain_name, 'hypercloud.io')
        self.assertEqual(site.industry.slug, 'technology-and-it')
        self.assertIn('services_list', site.custom_data)

        # Test website preview page
        preview_res = self.client.get(reverse('website_preview', kwargs={'site_id': site.site_id}))
        self.assertEqual(preview_res.status_code, 200)
        self.assertContains(preview_res, 'HyperCloud Infrastructure')

        # Test standalone website template
        standalone_res = self.client.get(reverse('website_standalone', kwargs={'slug': site.slug}))
        self.assertEqual(standalone_res.status_code, 200)
        self.assertContains(standalone_res, 'HyperCloud Infrastructure')
        self.assertContains(standalone_res, 'Next-Gen Serverless Hosting')

    def test_signup_get(self):
        res = self.client.get(reverse('signup'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Create your account")
        self.assertContains(res, "BrandNest ID")

    def test_signup_post_success(self):
        post_data = {
            'full_name': 'Yash Manoj',
            'email': 'yash@brandnest.io',
            'username': 'yashmanoj',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        }
        res = self.client.post(reverse('signup'), post_data)
        self.assertEqual(res.status_code, 302)  # Redirects to landing or next
        
        # Verify user created and authenticated
        from django.contrib.auth.models import User
        user = User.objects.get(email='yash@brandnest.io')
        self.assertEqual(user.username, 'yashmanoj')
        self.assertEqual(user.first_name, 'Yash')
        self.assertEqual(user.last_name, 'Manoj')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_signup_post_password_mismatch(self):
        post_data = {
            'full_name': 'Test User',
            'email': 'test@brandnest.io',
            'password': 'Password123',
            'confirm_password': 'DifferentPassword456',
        }
        res = self.client.post(reverse('signup'), post_data)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Passwords do not match")

    def test_login_get(self):
        res = self.client.get(reverse('login'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Welcome back")
        self.assertContains(res, "Sign in to BrandNest")

    def test_login_post_by_username(self):
        from django.contrib.auth.models import User
        User.objects.create_user(username='alexv', email='alex@brandnest.io', password='TestSecretPassword123')

        res = self.client.post(reverse('login'), {
            'login_identifier': 'alexv',
            'password': 'TestSecretPassword123'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_post_by_email(self):
        from django.contrib.auth.models import User
        User.objects.create_user(username='sarahc', email='sarah@brandnest.io', password='TestSecretPassword123')

        # Login using email instead of username
        res = self.client.post(reverse('login'), {
            'login_identifier': 'sarah@brandnest.io',
            'password': 'TestSecretPassword123'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_post_invalid_credentials(self):
        res = self.client.post(reverse('login'), {
            'login_identifier': 'nonexistent@brandnest.io',
            'password': 'WrongPassword!'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Invalid email/username or password")

    def test_logout(self):
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='logoutuser', email='logout@brandnest.io', password='Password123')
        self.client.force_login(user)
        self.assertTrue('_auth_user_id' in self.client.session)

        res = self.client.get(reverse('logout'))
        self.assertEqual(res.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)
