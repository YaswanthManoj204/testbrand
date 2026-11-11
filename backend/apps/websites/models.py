import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from apps.domains.models import Domain


class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-briefcase', help_text="Bootstrap icon class")
    form_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON schema specifying custom fields and sections for this industry"
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Industries'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Website(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('preview_ready', 'Preview Ready'),
        ('provisioning', 'Provisioning Hosting'),
        ('deploying', 'Deploying Files'),
        ('domain_pending', 'Domain Pending'),
        ('ssl_pending', 'SSL Pending'),
        ('published', 'Published'),
        ('failed', 'Deployment Failed'),
        ('suspended', 'Suspended'),
    ]

    site_id = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='websites')
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True, blank=True, related_name='websites')
    industry = models.ForeignKey(Industry, on_delete=models.PROTECT, related_name='websites')

    # Core Branding & Hero
    title = models.CharField(max_length=200, help_text="Company or Website Name")
    tagline = models.CharField(max_length=255, blank=True, help_text="Short slogan or hero headline")
    about_text = models.TextField(blank=True, help_text="Company introduction / About Us")
    logo = models.ImageField(upload_to='websites/logos/', null=True, blank=True)
    hero_image = models.ImageField(upload_to='websites/heroes/', null=True, blank=True)
    
    # Theme settings
    primary_color = models.CharField(max_length=20, default='#1E40AF')
    secondary_color = models.CharField(max_length=20, default='#0EA5E9')

    # Contact & Location
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    working_hours = models.CharField(max_length=150, blank=True)
    maps_url = models.URLField(max_length=500, blank=True)

    # Social links
    social_links = models.JSONField(default=dict, blank=True)

    # Dynamic Industry Specific Data
    # Contains structured JSON like:
    # - Services, products, team, testimonials, menu_items, doctors, etc.
    custom_data = models.JSONField(default=dict, blank=True)

    # Publishing lifecycle
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    published_version = models.PositiveIntegerField(default=1)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.site_id}) - {self.industry.name}"

    def save(self, *args, **kwargs):
        if not self.site_id:
            self.site_id = f"SITE-{uuid.uuid4().hex[:8].upper()}"
        if not self.slug:
            base_slug = slugify(self.title) or "website"
            candidate = base_slug
            counter = 1
            while Website.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def live_url(self):
        if self.domain:
            return f"https://{self.domain.domain_name}"
        return f"/site/{self.slug}/"


class WebsitePage(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='pages')
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    meta_description = models.CharField(max_length=255, blank=True)
    content_blocks = models.JSONField(default=list, blank=True)
    is_home = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        unique_together = ('website', 'slug')

    def __str__(self):
        return f"{self.website.title} - {self.title}"


class ContactSubmission(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='enquiries')
    visitor_name = models.CharField(max_length=150)
    visitor_email = models.EmailField()
    visitor_phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Enquiry from {self.visitor_name} on {self.website.title}"
