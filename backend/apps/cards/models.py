import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from apps.domains.models import Domain


class BusinessCard(models.Model):
    card_id = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards')
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards')

    # Basic business info
    business_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    services = models.TextField(blank=True, help_text="Comma-separated or bullet points of services offered")

    # Visual assets
    logo = models.ImageField(upload_to='cards/logos/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='cards/banners/', null=True, blank=True)
    profile_image = models.ImageField(upload_to='cards/profiles/', null=True, blank=True)
    theme_color = models.CharField(max_length=20, default='#2563EB')

    # Direct contact actions
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    google_maps_url = models.URLField(max_length=500, blank=True)
    existing_website = models.URLField(blank=True)

    # Social links structured as JSON
    social_links = models.JSONField(default=dict, blank=True, help_text="Dict of platform: url (linkedin, instagram, etc.)")

    # Drag & drop customizable layout order and section configurations
    layout_config = models.JSONField(default=dict, blank=True, help_text="Custom section order, capabilities, brands, tabs and theme")

    # Publishing and sharing
    is_published = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business_name} ({self.card_id})"

    def save(self, *args, **kwargs):
        if not self.card_id:
            self.card_id = f"CARD-{uuid.uuid4().hex[:8].upper()}"
        if not self.slug:
            base_slug = slugify(self.business_name) or "business-card"
            candidate = base_slug
            counter = 1
            while BusinessCard.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def share_url(self):
        if self.domain:
            return f"https://{self.domain.domain_name}"
        return f"/card/{self.slug}/"
