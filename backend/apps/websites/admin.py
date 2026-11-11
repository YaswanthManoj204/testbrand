from django.contrib import admin
from django.utils.html import format_html
from .models import Industry, Website, WebsitePage, ContactSubmission


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'display_order')


class WebsitePageInline(admin.TabularInline):
    model = WebsitePage
    extra = 1


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('title', 'site_id', 'industry', 'status', 'is_published', 'views_count', 'preview_action_link', 'created_at')
    list_filter = ('industry', 'status', 'is_published', 'created_at')
    search_fields = ('title', 'site_id', 'contact_email', 'contact_phone')
    readonly_fields = ('site_id', 'slug', 'views_count', 'created_at', 'updated_at', 'preview_action_link')
    inlines = [WebsitePageInline]

    @admin.display(description='Live Website')
    def preview_action_link(self, obj):
        if not obj.pk:
            return '-'
        public_url = f"/site/{obj.slug}/"
        return format_html(
            '<a class="btn btn-xs btn-primary" href="{}" target="_blank"><i class="fas fa-globe"></i> View Site</a>',
            public_url
        )


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('visitor_name', 'website', 'visitor_email', 'visitor_phone', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('visitor_name', 'visitor_email', 'message')
