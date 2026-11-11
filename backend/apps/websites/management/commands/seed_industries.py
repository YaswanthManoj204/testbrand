from django.core.management.base import BaseCommand
from apps.websites.models import Industry


INDUSTRIES_DATA = [
    {
        "name": "Technology and IT",
        "slug": "technology-and-it",
        "icon": "bi-cpu",
        "display_order": 1,
        "description": "Software companies, IT services, SaaS startups, and digital agencies.",
        "form_schema": {
            "sections": [
                {
                    "id": "services",
                    "title": "Core IT Services",
                    "fields": [
                        {"name": "services_list", "label": "Services Offered", "type": "textarea", "placeholder": "e.g. Cloud Architecture, Mobile App Development, AI Solutions", "required": True},
                        {"name": "tech_stack", "label": "Technologies & Frameworks", "type": "text", "placeholder": "e.g. Python, React, AWS, Docker"}
                    ]
                },
                {
                    "id": "portfolio",
                    "title": "Projects & Products",
                    "fields": [
                        {"name": "featured_projects", "label": "Key Projects or Products", "type": "textarea", "placeholder": "Describe 2-3 highlighted projects or SaaS products"},
                        {"name": "client_count", "label": "Clients Served or Stat Callout", "type": "text", "placeholder": "e.g. 150+ Happy Clients Globally"}
                    ]
                }
            ]
        }
    },
    {
        "name": "Healthcare & Clinics",
        "slug": "healthcare",
        "icon": "bi-heart-pulse",
        "display_order": 2,
        "description": "Hospitals, medical clinics, specialized doctors, and dental practices.",
        "form_schema": {
            "sections": [
                {
                    "id": "medical_services",
                    "title": "Medical Treatments & Departments",
                    "fields": [
                        {"name": "departments", "label": "Departments & Specialties", "type": "textarea", "placeholder": "e.g. Cardiology, Pediatrics, General Medicine, Dermatology", "required": True},
                        {"name": "treatments", "label": "Key Treatments Offered", "type": "textarea", "placeholder": "List specialized procedures or outpatient services"}
                    ]
                },
                {
                    "id": "appointments",
                    "title": "Doctor & Appointment Details",
                    "fields": [
                        {"name": "lead_doctor", "label": "Lead Doctor / Medical Director", "type": "text", "placeholder": "e.g. Dr. Sarah Jenkins, MD"},
                        {"name": "emergency_contact", "label": "Emergency Helpline Number", "type": "text", "placeholder": "e.g. +1 (800) 555-EMERGENCY"}
                    ]
                }
            ]
        }
    },
    {
        "name": "Restaurants & Cafes",
        "slug": "restaurants",
        "icon": "bi-cup-hot",
        "display_order": 3,
        "description": "Restaurants, dining cafes, bakeries, bars, and food catering businesses.",
        "form_schema": {
            "sections": [
                {
                    "id": "cuisine",
                    "title": "Cuisine & Dining Style",
                    "fields": [
                        {"name": "cuisine_type", "label": "Cuisine Specialty", "type": "text", "placeholder": "e.g. Italian Fine Dining, Artisanal Coffee & Pastries", "required": True},
                        {"name": "specialty_dishes", "label": "Signature Menu Items", "type": "textarea", "placeholder": "e.g. Truffle Woodfired Pizza, Handcrafted Tiramisu, Organic Cold Brew"}
                    ]
                },
                {
                    "id": "reservation",
                    "title": "Dine-in & Reservations",
                    "fields": [
                        {"name": "reservation_phone", "label": "Table Booking Contact", "type": "text", "placeholder": "e.g. +1 (555) 019-2834"},
                        {"name": "service_options", "label": "Dining Options", "type": "text", "placeholder": "e.g. Dine-in • Curbside Pickup • Private Events"}
                    ]
                }
            ]
        }
    },
    {
        "name": "Education & Academies",
        "slug": "education",
        "icon": "bi-mortarboard",
        "display_order": 4,
        "description": "Schools, colleges, training centers, coding bootcamps, and academies.",
        "form_schema": {
            "sections": [
                {
                    "id": "programs",
                    "title": "Academic Programs & Courses",
                    "fields": [
                        {"name": "courses_list", "label": "Offered Courses / Programs", "type": "textarea", "placeholder": "e.g. Full Stack Web Development, Data Science Bootcamp", "required": True},
                        {"name": "accreditation", "label": "Accreditations & Certifications", "type": "text", "placeholder": "e.g. Nationally Accredited, ISO Certified"}
                    ]
                },
                {
                    "id": "admissions",
                    "title": "Admissions & Faculty",
                    "fields": [
                        {"name": "faculty_highlight", "label": "Faculty / Instructor Highlight", "type": "textarea", "placeholder": "e.g. 50+ Industry expert instructors from top tech firms"},
                        {"name": "admission_deadline", "label": "Upcoming Batch or Admission Deadline", "type": "text", "placeholder": "e.g. Spring 2026 Batch Starting April 15"}
                    ]
                }
            ]
        }
    },
    {
        "name": "Construction & Contractors",
        "slug": "construction",
        "icon": "bi-tools",
        "display_order": 5,
        "description": "Commercial builders, residential contractors, renovators, and civil engineers.",
        "form_schema": {
            "sections": [
                {
                    "id": "capabilities",
                    "title": "Construction Capabilities",
                    "fields": [
                        {"name": "construction_services", "label": "Services Provided", "type": "textarea", "placeholder": "e.g. Commercial Construction, Residential Renovation, Civil Engineering", "required": True},
                        {"name": "license_info", "label": "License & Insurance Info", "type": "text", "placeholder": "e.g. Licensed General Contractor #GC-98214 - Fully Insured"}
                    ]
                },
                {
                    "id": "past_works",
                    "title": "Track Record",
                    "fields": [
                        {"name": "notable_projects", "label": "Completed Projects Highlight", "type": "textarea", "placeholder": "e.g. Downtown Plaza (50,000 sq ft), Green Ridge Luxury Villas"}
                    ]
                }
            ]
        }
    },
    {
        "name": "Real Estate & Agencies",
        "slug": "real-estate",
        "icon": "bi-buildings",
        "display_order": 6,
        "description": "Property brokers, real estate agencies, luxury residential developers, and rentals.",
        "form_schema": {
            "sections": [
                {
                    "id": "property_focus",
                    "title": "Property Portfolio Focus",
                    "fields": [
                        {"name": "property_types", "label": "Specialization", "type": "text", "placeholder": "e.g. Luxury Condos, Commercial Leases, Suburban Family Homes", "required": True},
                        {"name": "featured_locations", "label": "Prime Neighborhoods / Locations", "type": "textarea", "placeholder": "e.g. Manhattan, Brooklyn Heights, Long Island City"}
                    ]
                },
                {
                    "id": "agent_services",
                    "title": "Buyer & Seller Services",
                    "fields": [
                        {"name": "broker_license", "label": "Brokerage License / Board", "type": "text", "placeholder": "e.g. Certified Realtor - Board of Realtors Member"},
                        {"name": "valuation_offer", "label": "Free Appraisal Offer Text", "type": "text", "placeholder": "e.g. Complimentary Instant Home Valuation"}
                    ]
                }
            ]
        }
    },
    {
        "name": "E-commerce & Stores",
        "slug": "e-commerce",
        "icon": "bi-cart3",
        "display_order": 7,
        "description": "Retailers, fashion brands, artisanal product creators, and online stores.",
        "form_schema": {
            "sections": [
                {
                    "id": "store_catalog",
                    "title": "Product Categories & Lines",
                    "fields": [
                        {"name": "product_categories", "label": "Product Categories", "type": "textarea", "placeholder": "e.g. Organic Skincare, Handcrafted Leather Bags, Apparel", "required": True},
                        {"name": "shipping_policy", "label": "Shipping & Guarantee Highlight", "type": "text", "placeholder": "e.g. Free Worldwide Express Shipping on Orders Over $75"}
                    ]
                }
            ]
        }
    },
    {
        "name": "Professional Services & Other",
        "slug": "professional-services",
        "icon": "bi-briefcase",
        "display_order": 8,
        "description": "Law firms, accountants, consultants, creative agencies, and local services.",
        "form_schema": {
            "sections": [
                {
                    "id": "consulting",
                    "title": "Practice Areas & Consulting",
                    "fields": [
                        {"name": "practice_areas", "label": "Practice Areas / Expertise", "type": "textarea", "placeholder": "e.g. Corporate Tax Advisory, IP Law, Strategic Brand Consulting", "required": True},
                        {"name": "experience_years", "label": "Years in Business / Experience", "type": "text", "placeholder": "e.g. Over 20 Years of Trusted Advisory"}
                    ]
                }
            ]
        }
    }
]


class Command(BaseCommand):
    help = "Seeds initial industry categories and their dynamic form schemas"

    def handle(self, *args, **options):
        self.stdout.write("Seeding industries...")
        created_count = 0
        updated_count = 0

        for item in INDUSTRIES_DATA:
            industry, created = Industry.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "icon": item["icon"],
                    "display_order": item["display_order"],
                    "description": item["description"],
                    "form_schema": item["form_schema"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully processed industries: {created_count} created, {updated_count} updated.")
        )

