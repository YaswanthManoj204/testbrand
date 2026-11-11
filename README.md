# BrandNest - Digital Business Card & Website Builder SaaS

BrandNest is a complete digital presence builder platform that enables individuals, entrepreneurs, and businesses to establish their online identity without technical or programming experience.

The platform provides two primary modules:
1. **Build a Business Card**: Generate a responsive, mobile-optimized digital business card with click-to-call, click-to-email, WhatsApp, Google Maps, vCard export, and shareable QR codes.
2. **Make Your Own Website**: Generate multi-section, industry-specific business websites (Technology, Healthcare, Restaurants, Education, Construction, Real Estate, E-commerce, Professional Services) with tailored dynamic fields, multi-device viewports, and working inquiry submissions.

Both modules feature a **domain-first connection gate** where users connect and verify their custom domain before entering business details.

---

## Technical Architecture

- **Backend**: Python 3.14 + Django 6.1 + Django REST Framework + CORS Headers
- **Database**: PostgreSQL (with automatic zero-config SQLite development fallback)
- **Frontend**: Bootstrap 5.3 + Bootstrap Icons + Custom Device Viewports & Mockups
- **Multi-Tenant Deployment Ready**: Reusable template engine designed for Hostinger Cloud Hosting

---

## Quick Start (Local Development)

### 1. Activate Environment
```bash
source venv/bin/activate
```

### 2. Run Database Migrations & Seed Initial Industries
```bash
cd backend
python manage.py migrate
python manage.py seed_industries
```

### 3. Run the Platform Server
```bash
python manage.py runserver 8000
```
Open your browser and navigate to:
- **Main Landing Page**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Module 1 (Business Card Builder)**: [http://127.0.0.1:8000/card/create/](http://127.0.0.1:8000/card/create/)
- **Module 2 (Website Builder)**: [http://127.0.0.1:8000/website/create/](http://127.0.0.1:8000/website/create/)
- **REST API Health & Stats**: [http://127.0.0.1:8000/api/v1/health/](http://127.0.0.1:8000/api/v1/health/)
- **Django Admin Portal**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Automated Test Suite
To run all API and frontend workflow tests:
```bash
cd backend
python manage.py test apps.api apps.frontend
```

