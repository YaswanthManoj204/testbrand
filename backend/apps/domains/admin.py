from django.contrib import admin
from .models import Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain_name', 'domain_type', 'verification_status', 'ssl_status', 'created_at')
    list_filter = ('domain_type', 'verification_status', 'ssl_status')
    search_fields = ('domain_name', 'verification_token')
    readonly_fields = ('verification_token', 'created_at', 'updated_at')
