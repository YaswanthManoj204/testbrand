import secrets
from django.db import models
from django.contrib.auth.models import User


class Domain(models.Model):
    TYPE_CHOICES = [
        ('custom', 'Custom Domain'),
        ('subdomain', 'Platform Subdomain'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('failed', 'Verification Failed'),
    ]

    SSL_CHOICES = [
        ('pending', 'Pending SSL'),
        ('active', 'Active SSL'),
        ('failed', 'SSL Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='domains')
    domain_name = models.CharField(max_length=255, unique=True, db_index=True)
    domain_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='custom')
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_token = models.CharField(max_length=64, blank=True)
    ssl_status = models.CharField(max_length=20, choices=SSL_CHOICES, default='pending')
    
    target_cname = models.CharField(max_length=255, default='cname.brandnest.live')
    target_ip = models.CharField(max_length=45, default='185.199.108.153')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.domain_name} ({self.get_verification_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-clean domain name (lowercase, strip protocol and paths)
        clean_name = self.domain_name.strip().lower()
        clean_name = clean_name.replace('http://', '').replace('https://', '').split('/')[0]
        self.domain_name = clean_name

        if not self.verification_token:
            self.verification_token = f"brandnest-verify-{secrets.token_hex(16)}"
        super().save(*args, **kwargs)

    @property
    def txt_record_name(self):
        return f"_brandnest-challenge.{self.domain_name}"

    @property
    def is_ready(self):
        return self.verification_status == 'verified'
