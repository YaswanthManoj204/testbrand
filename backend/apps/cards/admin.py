from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import BusinessCard


@admin.register(BusinessCard)
class BusinessCardAdmin(admin.ModelAdmin):
    list_display = (
        'business_name',
        'owner_name',
        'card_id',
        'status_badge',
        'views_count',
        'preview_action_links',
        'created_at',
    )
    list_filter = ('is_published', 'created_at', 'theme_color')
    search_fields = ('business_name', 'owner_name', 'card_id', 'slug', 'phone', 'email')
    readonly_fields = ('card_id', 'slug', 'views_count', 'created_at', 'updated_at', 'preview_action_links')
    actions = ['make_published', 'make_unpublished', 'reset_views']

    fieldsets = (
        ('Card Identity & Ownership', {
            'fields': (
                'business_name',
                'owner_name',
                'tagline',
                'bio',
                'theme_color',
            )
        }),
        ('Visual Assets', {
            'fields': (
                'profile_photo',
                'logo',
                'banner_image',
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone',
                'email',
                'website',
                'address',
                'social_links',
            )
        }),
        ('SaaS Layout & Section Configuration', {
            'classes': ('collapse',),
            'fields': (
                'layout_config',
            )
        }),
        ('System Metadata & Live Actions', {
            'fields': (
                'card_id',
                'slug',
                'is_published',
                'views_count',
                'preview_action_links',
                'created_at',
                'updated_at',
            )
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_published:
            return format_html('<span class="badge badge-success px-2 py-1"><i class="fas fa-check-circle"></i> Published</span>')
        return format_html('<span class="badge badge-secondary px-2 py-1"><i class="fas fa-pencil-alt"></i> Draft</span>')

    @admin.display(description='Actions')
    def preview_action_links(self, obj):
        if not obj.pk:
            return '-'
        preview_url = f"/card/preview/{obj.card_id}/"
        public_url = f"/card/{obj.slug}/"
        edit_url = f"/card/edit/{obj.card_id}/"
        admin_delete_url = reverse('admin:cards_businesscard_delete', args=[obj.pk])
        return format_html(
            '<a class="btn btn-xs btn-warning text-dark mr-1" href="{}" target="_blank" title="Edit in Card Builder"><i class="fas fa-edit"></i> Edit</a> '
            '<a class="btn btn-xs btn-primary mr-1" href="{}" target="_blank" title="Preview Card"><i class="fas fa-mobile-alt"></i> Preview</a> '
            '<a class="btn btn-xs btn-info mr-1" href="{}" target="_blank" title="Public Standalone Card"><i class="fas fa-external-link-alt"></i> Live</a> '
            '<a class="btn btn-xs btn-danger" href="{}" title="Delete Card"><i class="fas fa-trash-alt"></i> Delete</a>',
            edit_url,
            preview_url,
            public_url,
            admin_delete_url
        )

    @admin.action(description='Mark selected cards as Published')
    def make_published(self, request, queryset):
        rows = queryset.update(is_published=True)
        self.message_user(request, f"{rows} business card(s) marked as published.")

    @admin.action(description='Mark selected cards as Draft / Unpublished')
    def make_unpublished(self, request, queryset):
        rows = queryset.update(is_published=False)
        self.message_user(request, f"{rows} business card(s) marked as unpublished draft.")

    @admin.action(description='Reset view counts for selected cards')
    def reset_views(self, request, queryset):
        rows = queryset.update(views_count=0)
        self.message_user(request, f"Views counter reset to 0 for {rows} card(s).")
