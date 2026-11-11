import os
import re
import json
import subprocess
import shutil
import urllib.request
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import Http404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.text import slugify

from apps.domains.models import Domain
from apps.cards.models import BusinessCard
from apps.websites.models import Industry, Website, ContactSubmission


def get_lan_ip():
    """
    Detects local Wi-Fi / LAN IP so phones on the same network can access dev server directly.
    """
    try:
        if shutil.which('ipconfig'):
            for iface in ['en0', 'en1', 'wlan0', 'eth0']:
                res = subprocess.run(['ipconfig', 'getifaddr', iface], capture_output=True, text=True, timeout=1)
                ip = res.stdout.strip()
                if ip and re.match(r'^\d+\.\d+\.\d+\.\d+$', ip) and not ip.startswith('127.'):
                    return ip
    except Exception:
        pass
    return None


def get_shareable_url(request, path):
    """
    Builds a direct, reliable shareable URL for QR codes.
    1. If request is from localhost/127.0.0.1, uses the machine's local Wi-Fi LAN IP (e.g. http://192.168.1.42:8000/card/<slug>/)
       so phones on the same Wi-Fi can scan and open it directly without Cloudflare tunnel errors.
    2. Otherwise uses the absolute request URI (works on production domains, remote servers or direct IP).
    """
    host = request.get_host()
    if '127.0.0.1' in host or 'localhost' in host:
        lan_ip = get_lan_ip()
        if lan_ip:
            port = host.split(':')[1] if ':' in host else '8000'
            return f"http://{lan_ip}:{port}{path}"
    return request.build_absolute_uri(path)


def generate_qr_code_image_bytes(data_url):
    """
    Generates a high-resolution QR code PNG directly via Python's qrcode library.
    Includes a fallback in case qrcode/Pillow is temporarily unavailable.
    """
    import io
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except Exception:
        # Fallback to pure urllib fetching or clean SVG/PNG fallback
        import urllib.request
        import urllib.parse
        encoded_data = urllib.parse.quote(data_url)
        try:
            with urllib.request.urlopen(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_data}", timeout=3) as resp:
                return resp.read()
        except Exception:
            return b""


def generate_qr_code_base64(data_url):
    """
    Generates a base64 data URI (data:image/png;base64,...) using Python's qrcode library.
    Generates freshly on each page render or refresh.
    """
    import base64
    raw_bytes = generate_qr_code_image_bytes(data_url)
    encoded = base64.b64encode(raw_bytes).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


def landing(request):
    """
    Landing Page: Displays the two primary choices:
    1. Build a Business Card
    2. Make Your Own Website
    """
    industries = Industry.objects.filter(is_active=True).order_by('display_order')
    total_cards = BusinessCard.objects.count()
    total_websites = Website.objects.count()
    total_industries = industries.count()

    context = {
        'industries': industries,
        'total_cards': total_cards,
        'total_websites': total_websites,
        'total_industries': total_industries,
    }
    return render(request, 'landing.html', context)


def card_builder(request, card_id=None):
    """
    Business Card Builder:
    Step 1: Enter Business, Contact & Social Details
    (No custom domain required - includes optional website link or 1-click builder link)
    Step 2: Instant Card Preview & Sharing
    If card_id is provided, edits and updates the existing Business Card.
    """
    target_card = None
    if card_id:
        target_card = get_object_or_404(BusinessCard, card_id=card_id)

    if request.method == 'POST':
        business_name = request.POST.get('business_name', '').strip()

        if not business_name:
            messages.error(request, 'Please provide your business name.')
            return render(request, 'card_builder.html', {'card': target_card, 'is_edit': bool(target_card)})

        # 1. Extract Social Links (supports both form naming conventions)
        social_links = {
            'linkedin': (request.POST.get('linkedin') or request.POST.get('social_linkedin') or '').strip(),
            'youtube': (request.POST.get('youtube') or request.POST.get('social_youtube') or '').strip(),
            'instagram': (request.POST.get('instagram') or request.POST.get('social_instagram') or '').strip(),
            'twitter': (request.POST.get('twitter') or request.POST.get('social_twitter') or '').strip(),
            'facebook': (request.POST.get('facebook') or request.POST.get('social_facebook') or '').strip(),
        }

        # 2. Extract section order & disabled sections for custom layout
        section_order_raw = request.POST.get('section_order', '')
        section_order = []
        if section_order_raw:
            try:
                section_order = json.loads(section_order_raw)
            except Exception:
                section_order = [s.strip() for s in section_order_raw.split(',') if s.strip()]

        disabled_sections_raw = request.POST.get('disabled_sections', '')
        disabled_sections = []
        if disabled_sections_raw:
            try:
                disabled_sections = json.loads(disabled_sections_raw)
            except Exception:
                disabled_sections = [s.strip() for s in disabled_sections_raw.split(',') if s.strip()]

        # Extract dynamic capabilities & brands data
        capabilities_data_raw = request.POST.get('capabilities_data', '')
        capabilities_items = []
        if capabilities_data_raw:
            try:
                capabilities_items = json.loads(capabilities_data_raw)
                capabilities_items = [
                    item for item in capabilities_items
                    if (item.get('title') and item.get('title').strip()) or (item.get('description') and item.get('description').strip())
                ]
            except Exception:
                pass

        brands_data_raw = request.POST.get('brands_data', '')
        brands_items = []
        if brands_data_raw:
            try:
                brands_items = json.loads(brands_data_raw)
                brands_items = [
                    item for item in brands_items
                    if (item.get('title') and item.get('title').strip()) or (item.get('description') and item.get('description').strip())
                ]
            except Exception:
                pass

        role_title = request.POST.get('role_title', '').strip()
        owner_role = request.POST.get('owner_role', '').strip()
        owner_title = ''
        identity_order = request.POST.get('identity_order', 'company,role').strip()
        role_title_order = request.POST.get('role_title_order', 'company_first').strip()
        show_profile_photo = request.POST.get('show_profile_photo', 'true').lower() in ('true', '1', 'on')
        show_company_logo = request.POST.get('show_company_logo', 'true').lower() in ('true', '1', 'on')
        show_banner = request.POST.get('show_banner', 'true').lower() in ('true', '1', 'on')

        if owner_role:
            role_title = owner_role

        about_heading = request.POST.get('about_heading', '').strip()
        yt_channel_name = request.POST.get('yt_channel_name', '').strip()
        yt_subscribers = request.POST.get('yt_subscribers', '').strip()
        yt_description = request.POST.get('yt_description', '').strip()
        avatar_position = request.POST.get('avatar_position', '50% 50%').strip()
        avatar_x = request.POST.get('avatar_x', '').strip()
        avatar_y = request.POST.get('avatar_y', '').strip()
        avatar_zoom = request.POST.get('avatar_zoom', '1').strip() or '1'

        logo_position = request.POST.get('logo_position', '50% 50%').strip()
        logo_x = request.POST.get('logo_x', '').strip()
        logo_y = request.POST.get('logo_y', '').strip()
        logo_zoom = request.POST.get('logo_zoom', '1').strip() or '1'

        banner_position = request.POST.get('banner_position', '50% 50%').strip()
        banner_x = request.POST.get('banner_x', '').strip()
        banner_y = request.POST.get('banner_y', '').strip()
        banner_zoom = request.POST.get('banner_zoom', '1').strip() or '1'

        if not avatar_x or not avatar_y:
            try:
                parts = avatar_position.split()
                if len(parts) >= 2:
                    avatar_x = f"{float(parts[0].replace('%', '')) - 50:.1f}%"
                    avatar_y = f"{float(parts[1].replace('%', '')) - 50:.1f}%"
                else:
                    avatar_x, avatar_y = "0%", "0%"
            except Exception:
                avatar_x, avatar_y = "0%", "0%"

        if not logo_x or not logo_y:
            try:
                parts = logo_position.split()
                if len(parts) >= 2:
                    logo_x = f"{float(parts[0].replace('%', '')) - 50:.1f}%"
                    logo_y = f"{float(parts[1].replace('%', '')) - 50:.1f}%"
                else:
                    logo_x, logo_y = "0%", "0%"
            except Exception:
                logo_x, logo_y = "0%", "0%"

        if not banner_x or not banner_y:
            try:
                parts = banner_position.split()
                if len(parts) >= 2:
                    banner_x = f"{float(parts[0].replace('%', '')) - 50:.1f}%"
                    banner_y = f"{float(parts[1].replace('%', '')) - 50:.1f}%"
                else:
                    banner_x, banner_y = "0%", "0%"
            except Exception:
                banner_x, banner_y = "0%", "0%"
        card_layout = request.POST.get('card_layout', 'layout-cover-hero').strip() or 'layout-cover-hero'
        card_font = request.POST.get('card_font', 'Plus Jakarta Sans').strip() or 'Plus Jakarta Sans'
        wallet_config_raw = request.POST.get('wallet_config', '')
        wallet_config = {}
        if wallet_config_raw:
            try:
                wallet_config = json.loads(wallet_config_raw)
            except Exception:
                pass

        # Card Settings (from Settings Tab)
        settings_custom_domain = request.POST.get('settings_custom_domain', '').strip()
        settings_visibility = request.POST.get('settings_visibility', 'public').strip()
        settings_password = request.POST.get('settings_password', '').strip()
        settings_show_save_contact = request.POST.get('settings_show_save_contact', 'true').lower() in ('true', '1', 'on')
        settings_fb_chat_enabled = request.POST.get('settings_fb_chat_enabled', 'false').lower() in ('true', '1', 'on')
        settings_fb_page_id = request.POST.get('settings_fb_page_id', '').strip()
        settings_calendly_enabled = request.POST.get('settings_calendly_enabled', 'false').lower() in ('true', '1', 'on')
        settings_calendly_url = request.POST.get('settings_calendly_url', '').strip()
        settings_seo_index = request.POST.get('settings_seo_index', 'true').lower() in ('true', '1', 'on')
        settings_meta_title = request.POST.get('settings_meta_title', '').strip()
        settings_meta_desc = request.POST.get('settings_meta_desc', '').strip()
        settings_copyright = request.POST.get('settings_copyright', '').strip()
        settings_custom_js = request.POST.get('settings_custom_js', '').strip()
        settings_sensitive = request.POST.get('settings_sensitive', 'none').strip()
        settings_language = request.POST.get('settings_language', 'en').strip()

        card_settings = {
            'custom_domain': settings_custom_domain,
            'visibility': settings_visibility,
            'password': settings_password,
            'show_save_contact': settings_show_save_contact,
            'fb_chat_enabled': settings_fb_chat_enabled,
            'fb_page_id': settings_fb_page_id,
            'calendly_enabled': settings_calendly_enabled,
            'calendly_url': settings_calendly_url,
            'seo_index': settings_seo_index,
            'meta_title': settings_meta_title,
            'meta_description': settings_meta_desc,
            'copyright': settings_copyright,
            'custom_js': settings_custom_js,
            'sensitive_material': settings_sensitive,
            'language': settings_language,
        }

        # Payments configuration
        payments_data = {
            'gpay_enabled': request.POST.get('payment_gpay_enabled', 'true').lower() in ('true', '1', 'on'),
            'gpay': request.POST.get('payment_gpay', '').strip(),
            'phonepe_enabled': request.POST.get('payment_phonepe_enabled', 'true').lower() in ('true', '1', 'on'),
            'phonepe': request.POST.get('payment_phonepe', '').strip(),
            'paytm_enabled': request.POST.get('payment_paytm_enabled', 'true').lower() in ('true', '1', 'on'),
            'paytm': request.POST.get('payment_paytm', '').strip(),
            'paypal_enabled': request.POST.get('payment_paypal_enabled', 'true').lower() in ('true', '1', 'on'),
            'paypal': request.POST.get('payment_paypal', '').strip(),
            'venmo_enabled': request.POST.get('payment_venmo_enabled', 'true').lower() in ('true', '1', 'on'),
            'venmo': request.POST.get('payment_venmo', '').strip(),
            'cashapp_enabled': request.POST.get('payment_cashapp_enabled', 'true').lower() in ('true', '1', 'on'),
            'cashapp': request.POST.get('payment_cashapp', '').strip(),
            'razorpay_enabled': request.POST.get('payment_razorpay_enabled', 'true').lower() in ('true', '1', 'on'),
            'razorpay': request.POST.get('payment_razorpay', '').strip(),
        }

        # More section (Document with File or URL, Google Drive, Address)
        more_doc_url = request.POST.get('more_doc_url', '').strip() or request.POST.get('more_pdf_url', '').strip()
        if 'more_doc_file' in request.FILES:
            doc_file = request.FILES['more_doc_file']
            from django.core.files.storage import default_storage
            saved_doc_path = default_storage.save(f'cards/documents/{doc_file.name}', doc_file)
            more_doc_url = default_storage.url(saved_doc_path)
        elif 'more_pdf_file' in request.FILES:
            pdf_file = request.FILES['more_pdf_file']
            from django.core.files.storage import default_storage
            saved_pdf_path = default_storage.save(f'cards/documents/{pdf_file.name}', pdf_file)
            more_doc_url = default_storage.url(saved_pdf_path)

        more_data = {
            'doc_enabled': request.POST.get('more_doc_enabled', 'true').lower() in ('true', '1', 'on'),
            'doc_title': (request.POST.get('more_doc_title') or request.POST.get('more_pdf_title') or 'Document').strip(),
            'doc_url': more_doc_url,
            'pdf_title': (request.POST.get('more_doc_title') or request.POST.get('more_pdf_title') or 'Document').strip(),
            'pdf_url': more_doc_url,
            'gdrive_enabled': request.POST.get('more_gdrive_enabled', 'true').lower() in ('true', '1', 'on'),
            'gdrive_title': request.POST.get('more_gdrive_title', '').strip(),
            'gdrive_url': request.POST.get('more_gdrive_url', '').strip(),
        }

        layout_config = {
            'role_title': role_title,
            'owner_role': owner_role,
            'owner_title': owner_title,
            'identity_order': identity_order,
            'role_title_order': role_title_order,
            'show_profile_photo': show_profile_photo,
            'show_company_logo': show_company_logo,
            'show_banner': show_banner,
            'about_heading': about_heading,
            'capabilities_items': capabilities_items,
            'brands_items': brands_items,
            'avatar_x': avatar_x,
            'avatar_y': avatar_y,
            'avatar_position': avatar_position,
            'avatar_zoom': avatar_zoom,
            'logo_x': logo_x,
            'logo_y': logo_y,
            'logo_position': logo_position,
            'logo_zoom': logo_zoom,
            'banner_x': banner_x,
            'banner_y': banner_y,
            'banner_position': banner_position,
            'banner_zoom': banner_zoom,
            'layout_style': card_layout,
            'font': card_font,
            'wallet_config': wallet_config,
            'settings': card_settings,
            'yt_channel_name': yt_channel_name,
            'yt_subscribers': yt_subscribers,
            'yt_description': yt_description,
            'payments': payments_data,
            'more': more_data,
            'section_order': section_order,
            'disabled_sections': disabled_sections,
        }

        # 3. Optional existing website link
        existing_website = (request.POST.get('website') or request.POST.get('existing_website') or '').strip()

        # Services summary string
        services_summary = request.POST.get('services', '').strip()
        if not services_summary and capabilities_items:
            services_summary = ', '.join([item.get('title', '') for item in capabilities_items if item.get('title')])

        # 4. Create or Update Business Card
        if target_card:
            card = target_card
            card.business_name = business_name
            card.owner_name = request.POST.get('owner_name', '').strip()
            card.tagline = role_title
            card.description = (request.POST.get('bio') or request.POST.get('description') or '').strip()
            card.services = services_summary
            card.phone = request.POST.get('phone', '').strip()
            card.email = request.POST.get('email', '').strip()
            card.whatsapp = request.POST.get('whatsapp', '').strip()
            card.address = request.POST.get('address', '').strip()
            card.google_maps_url = (request.POST.get('maps_link') or request.POST.get('google_maps_url') or '').strip()
            card.existing_website = existing_website
            card.theme_color = (request.POST.get('accent_color') or request.POST.get('accent_preset') or request.POST.get('theme_color') or '#0084FF').strip()
            card.social_links = social_links
            card.layout_config = layout_config
            card.is_published = True
        else:
            card = BusinessCard(
                user=request.user if request.user.is_authenticated else None,
                domain=None,
                business_name=business_name,
                owner_name=request.POST.get('owner_name', '').strip(),
                tagline=role_title,
                description=(request.POST.get('bio') or request.POST.get('description') or '').strip(),
                services=services_summary,
                phone=request.POST.get('phone', '').strip(),
                email=request.POST.get('email', '').strip(),
                whatsapp=request.POST.get('whatsapp', '').strip(),
                address=request.POST.get('address', '').strip(),
                google_maps_url=(request.POST.get('maps_link') or request.POST.get('google_maps_url') or '').strip(),
                existing_website=existing_website,
                theme_color=(request.POST.get('accent_color') or request.POST.get('accent_preset') or request.POST.get('theme_color') or '#0084FF').strip(),
                social_links=social_links,
                layout_config=layout_config,
                is_published=True
            )

        if 'company_logo' in request.FILES:
            card.logo = request.FILES['company_logo']
        elif 'logo' in request.FILES:
            card.logo = request.FILES['logo']

        if 'banner_image' in request.FILES:
            card.banner_image = request.FILES['banner_image']
        elif 'banner' in request.FILES:
            card.banner_image = request.FILES['banner']

        if 'owner_photo' in request.FILES:
            card.profile_image = request.FILES['owner_photo']
        elif 'profile_image' in request.FILES:
            card.profile_image = request.FILES['profile_image']

        if settings_custom_domain:
            custom_slug_clean = slugify(settings_custom_domain.replace('.brandnest.me', '').replace('.qkbiz.com', '').strip())
            if custom_slug_clean and not BusinessCard.objects.filter(slug=custom_slug_clean).exclude(pk=card.pk).exists():
                card.slug = custom_slug_clean

        card.save()
        if target_card:
            messages.success(request, f'Business card for "{card.business_name}" updated successfully!')
        else:
            messages.success(request, f'Your digital business card for "{card.business_name}" has been generated!')
        return redirect('card_preview', card_id=card.card_id)

    default_card = BusinessCard(
        business_name="",
        owner_name="",
        tagline="",
        description="",
        services="",
        phone="",
        email="",
        whatsapp="",
        address="",
        google_maps_url="",
        existing_website="",
        theme_color="#0084FF",
        social_links={},
        layout_config={
            "banner_tagline": "",
            "role_title": "",
            "about_heading": "",
            "brands": "",
            "yt_channel_name": "",
            "yt_subscribers": "",
            "yt_description": "",
            "avatar_x": "0%",
            "avatar_y": "0%",
            "avatar_position": "50% 50%",
            "avatar_zoom": "1",
            "logo_x": "0%",
            "logo_y": "0%",
            "logo_position": "50% 50%",
            "logo_zoom": "1",
            "banner_x": "0%",
            "banner_y": "0%",
            "banner_position": "50% 50%",
            "banner_zoom": "1",
            "font": "Plus Jakarta Sans",
            "layout_style": "layout-cover-hero",
            "wallet_config": {},
            "settings": {
                "custom_domain": "",
                "visibility": "public",
                "password": "",
                "show_save_contact": True,
                "email_contact": True,
                "exchange_contact": True,
                "fb_chat_enabled": False,
                "fb_page_id": "",
                "calendly_enabled": False,
                "calendly_url": "",
                "seo_index": True,
                "meta_title": "",
                "meta_description": "",
                "copyright": "",
                "custom_js": "",
                "sensitive_material": "none",
                "language": "en"
            },
            "payments": {
                "gpay": "",
                "phonepe": "",
                "paytm": "",
                "paypal": "",
                "venmo": "",
                "cashapp": "",
                "razorpay": "",
            },
            "more": {
                "pdf_title": "",
                "pdf_url": "",
                "gdrive_title": "",
                "gdrive_url": "",
                "address": "",
                "maps_url": "",
            },
            "section_order": ["capabilities", "about", "brands", "connect", "payments", "more", "callback"],
            "disabled_sections": []
        }
    )
    if target_card:
        return render(request, 'card_builder.html', {'card': target_card, 'is_edit': True})
    return render(request, 'card_builder.html', {'card': default_card, 'is_edit': False})


def card_delete(request, card_id):
    """
    Delete a business card permanently.
    """
    card = get_object_or_404(BusinessCard, card_id=card_id)
    name = card.business_name or card.owner_name or 'Card'
    card.delete()
    messages.success(request, f'Business card "{name}" was successfully deleted.')
    if BusinessCard.objects.exists():
        return redirect('card_list')
    return redirect('card_builder')


def card_list(request):
    """
    SaaS Business Cards Manager:
    Lists all cards with status, views, preview link, edit in builder, and delete options.
    """
    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
        cards = BusinessCard.objects.all().order_by('-created_at')
    elif request.user.is_authenticated:
        cards = BusinessCard.objects.filter(user=request.user).order_by('-created_at')
    else:
        cards = BusinessCard.objects.all().order_by('-created_at')

    total_views = sum(c.views_count for c in cards) if cards else 0
    published_count = sum(1 for c in cards if c.is_published) if cards else 0

    return render(request, 'card_list.html', {
        'cards': cards,
        'total_count': cards.count() if hasattr(cards, 'count') else len(cards),
        'total_views': total_views,
        'published_count': published_count,
    })


def card_preview(request, card_id):
    """
    Presents the generated Business Card inside an interactive mobile preview device frame
    with share links, Python-generated QR code, and actions.
    """
    import time
    card = get_object_or_404(BusinessCard, card_id=card_id)
    standalone_path = reverse('card_standalone', kwargs={'slug': card.slug})
    share_url = get_shareable_url(request, standalone_path)
    qr_data_uri = generate_qr_code_base64(share_url)
    
    return render(request, 'card_preview.html', {
        'card': card,
        'share_url': share_url,
        'qr_data_uri': qr_data_uri,
        'timestamp': int(time.time()),
    })


def card_qr_image(request, slug):
    """
    Direct endpoint that returns a dynamically generated PNG QR code using python qrcode library.
    Generates a new QR code on each request/refresh without Cloudflare or external API.
    Supports ?download=1 to trigger attachment download.
    """
    from django.http import HttpResponse
    card = get_object_or_404(BusinessCard, slug=slug)
    standalone_path = reverse('card_standalone', kwargs={'slug': card.slug})
    share_url = get_shareable_url(request, standalone_path)

    png_bytes = generate_qr_code_image_bytes(share_url)
    response = HttpResponse(png_bytes, content_type='image/png')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    if request.GET.get('download') in ('1', 'true', 'yes'):
        filename = f"{card.slug}-qr.png"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@xframe_options_exempt
def card_standalone(request, slug):
    """
    Renders the live pre-made Business Card template full-screen (for visitor viewing).
    """
    card = get_object_or_404(BusinessCard, slug=slug)
    BusinessCard.objects.filter(pk=card.pk).update(views_count=card.views_count + 1)
    card.refresh_from_db()
    return render(request, 'card_template.html', {'card': card})


def website_builder(request):
    """
    Website Builder:
    Step 1: Connect Domain (Domain Gate)
    Step 2: Choose Industry Category
    Step 3: Fill Dynamic Industry Form
    Step 4: Generate Pre-made Industry Website & Preview
    """
    industries = Industry.objects.filter(is_active=True).order_by('display_order')

    if request.method == 'POST':
        domain_name = request.POST.get('domain_name', '').strip()
        industry_slug = request.POST.get('industry_slug', '').strip()
        title = request.POST.get('title', '').strip()

        if not domain_name:
            messages.error(request, 'Please provide and verify your domain name first.')
            return render(request, 'website_builder.html', {'industries': industries})

        if not industry_slug:
            messages.error(request, 'Please select an industry category.')
            return render(request, 'website_builder.html', {'industries': industries, 'domain_name': domain_name})

        industry = get_object_or_404(Industry, slug=industry_slug)

        # 1. Connect / Retrieve Domain
        domain, _ = Domain.objects.get_or_create(
            domain_name=domain_name,
            defaults={'domain_type': 'custom', 'verification_status': 'verified', 'ssl_status': 'active'}
        )
        if domain.verification_status != 'verified':
            domain.verification_status = 'verified'
            domain.ssl_status = 'active'
            domain.save()

        # 2. Extract Industry Dynamic Fields
        custom_data = {}
        for key, value in request.POST.items():
            if key.startswith('custom_'):
                clean_field_name = key.replace('custom_', '')
                custom_data[clean_field_name] = value.strip()

        # Extract Social Links
        social_links = {
            'linkedin': request.POST.get('social_linkedin', '').strip(),
            'instagram': request.POST.get('social_instagram', '').strip(),
            'twitter': request.POST.get('social_twitter', '').strip(),
            'facebook': request.POST.get('social_facebook', '').strip(),
        }

        # 3. Create Website
        website = Website(
            user=request.user if request.user.is_authenticated else None,
            domain=domain,
            industry=industry,
            title=title or f"{industry.name} Business",
            tagline=request.POST.get('tagline', '').strip(),
            about_text=request.POST.get('about_text', '').strip(),
            primary_color=request.POST.get('primary_color', '#1E40AF').strip() or '#1E40AF',
            contact_email=request.POST.get('contact_email', '').strip(),
            contact_phone=request.POST.get('contact_phone', '').strip(),
            address=request.POST.get('address', '').strip(),
            working_hours=request.POST.get('working_hours', '').strip(),
            social_links=social_links,
            custom_data=custom_data,
            status='published',
            is_published=True
        )

        if 'logo' in request.FILES:
            website.logo = request.FILES['logo']
        if 'hero_image' in request.FILES:
            website.hero_image = request.FILES['hero_image']

        website.save()
        messages.success(request, f'Your {industry.name} website for {website.title} is ready!')
        return redirect('website_preview', site_id=website.site_id)

    return render(request, 'website_builder.html', {'industries': industries})


def website_preview(request, site_id):
    """
    Website Preview: Provides desktop, tablet, and mobile device viewports
    and allows testing the interactive website.
    """
    website = get_object_or_404(Website, site_id=site_id)
    standalone_path = reverse('website_standalone', kwargs={'slug': website.slug})
    share_url = get_shareable_url(request, standalone_path)
    return render(request, 'website_preview.html', {
        'website': website,
        'share_url': share_url
    })


@xframe_options_exempt
def website_standalone(request, slug):
    """
    Renders the live pre-made Industry Website template full-screen (tenant live site).
    """
    website = get_object_or_404(Website, slug=slug)
    Website.objects.filter(pk=website.pk).update(views_count=website.views_count + 1)
    website.refresh_from_db()
    return render(request, 'website_template.html', {'website': website})


# ==============================================================================
# User Authentication Views (Signup, Login, Logout)
# ==============================================================================

def signup_view(request):
    """
    User Registration:
    Creates a new BrandNest user account, validates fields, and logs them in.
    """
    if request.user.is_authenticated:
        return redirect('landing')

    next_url = request.GET.get('next') or request.POST.get('next') or 'landing'

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Basic validations
        if not email:
            messages.error(request, 'Please provide a valid email address.')
            return render(request, 'signup.html', {
                'full_name': full_name,
                'email': email,
                'username': username,
                'next': next_url,
            })

        if not password:
            messages.error(request, 'Please enter a password.')
            return render(request, 'signup.html', {
                'full_name': full_name,
                'email': email,
                'username': username,
                'next': next_url,
            })

        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please re-enter your password.')
            return render(request, 'signup.html', {
                'full_name': full_name,
                'email': email,
                'username': username,
                'next': next_url,
            })

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'signup.html', {
                'full_name': full_name,
                'email': email,
                'username': username,
                'next': next_url,
            })

        # Auto-generate username from email if left blank
        if not username:
            base_username = email.split('@')[0]
            base_username = re.sub(r'[^a-zA-Z0-9._-]', '', base_username) or 'user'
            username = base_username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
        else:
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, f'Username "{username}" is already taken. Please choose another username.')
                return render(request, 'signup.html', {
                    'full_name': full_name,
                    'email': email,
                    'username': username,
                    'next': next_url,
                })

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, f'An account with email "{email}" already exists. Please log in.')
            return render(request, 'signup.html', {
                'full_name': full_name,
                'email': email,
                'username': username,
                'next': next_url,
            })

        # Split full name into first and last name
        first_name = ''
        last_name = ''
        if full_name:
            parts = full_name.split(' ', 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(request, user)
            display_name = full_name or user.username
            messages.success(request, f'Welcome to BrandNest, {display_name}! Your account has been created successfully.')
            return redirect(next_url)
        except Exception as e:
            messages.error(request, f'Error creating account: {e}')
            return render(request, 'signup.html', {
                'full_name': full_name,
                'email': email,
                'username': username,
                'next': next_url,
            })

    return render(request, 'signup.html', {'next': next_url})


def login_view(request):
    """
    User Login:
    Authenticates by either username OR email address, supports remember-me.
    """
    if request.user.is_authenticated:
        return redirect('landing')

    next_url = request.GET.get('next') or request.POST.get('next') or 'landing'

    if request.method == 'POST':
        login_identifier = request.POST.get('login_identifier', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        if not login_identifier or not password:
            messages.error(request, 'Please provide your email/username and password.')
            return render(request, 'login.html', {
                'login_identifier': login_identifier,
                'next': next_url,
            })

        # 1. Try authenticating directly with username
        user = authenticate(request, username=login_identifier, password=password)

        # 2. If failed, attempt looking up by email
        if user is None:
            try:
                user_obj = User.objects.get(email__iexact=login_identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None:
            if not user.is_active:
                messages.error(request, 'This account is currently inactive.')
                return render(request, 'login.html', {'login_identifier': login_identifier, 'next': next_url})

            login(request, user)
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Browser session expiry

            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email/username or password. Please verify your credentials.')
            return render(request, 'login.html', {
                'login_identifier': login_identifier,
                'next': next_url,
            })

    return render(request, 'login.html', {'next': next_url})


def logout_view(request):
    """
    User Logout:
    Cleans session and redirects to landing page.
    """
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('landing')
