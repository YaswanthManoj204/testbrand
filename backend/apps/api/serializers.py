from rest_framework import serializers
from apps.domains.models import Domain
from apps.cards.models import BusinessCard
from apps.websites.models import Industry, Website, WebsitePage, ContactSubmission


class DomainSerializer(serializers.ModelSerializer):
    txt_record_name = serializers.CharField(read_only=True)
    is_ready = serializers.BooleanField(read_only=True)

    class Meta:
        model = Domain
        fields = [
            'id',
            'domain_name',
            'domain_type',
            'verification_status',
            'verification_token',
            'txt_record_name',
            'target_cname',
            'target_ip',
            'ssl_status',
            'is_ready',
            'created_at',
        ]
        read_only_fields = ['id', 'verification_status', 'verification_token', 'ssl_status', 'created_at']


class DomainConnectSerializer(serializers.Serializer):
    domain_name = serializers.CharField(max_length=255)
    domain_type = serializers.ChoiceField(choices=['custom', 'subdomain'], default='custom')


class BusinessCardSerializer(serializers.ModelSerializer):
    domain_details = DomainSerializer(source='domain', read_only=True)
    share_url = serializers.CharField(read_only=True)

    class Meta:
        model = BusinessCard
        fields = '__all__'
        read_only_fields = ['id', 'card_id', 'slug', 'views_count', 'created_at', 'updated_at']


class BusinessCardPublicSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source='domain.domain_name', read_only=True, default='')

    class Meta:
        model = BusinessCard
        fields = [
            'card_id',
            'slug',
            'business_name',
            'owner_name',
            'tagline',
            'description',
            'services',
            'logo',
            'profile_image',
            'theme_color',
            'phone',
            'email',
            'whatsapp',
            'address',
            'google_maps_url',
            'existing_website',
            'social_links',
            'domain_name',
            'created_at',
        ]


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ['id', 'name', 'slug', 'description', 'icon', 'form_schema', 'display_order']


class WebsiteSerializer(serializers.ModelSerializer):
    domain_details = DomainSerializer(source='domain', read_only=True)
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    live_url = serializers.CharField(read_only=True)

    class Meta:
        model = Website
        fields = '__all__'
        read_only_fields = ['id', 'site_id', 'slug', 'views_count', 'created_at', 'updated_at']


class WebsitePublicSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    industry_slug = serializers.CharField(source='industry.slug', read_only=True)
    domain_name = serializers.CharField(source='domain.domain_name', read_only=True, default='')

    class Meta:
        model = Website
        fields = [
            'site_id',
            'slug',
            'title',
            'tagline',
            'about_text',
            'industry_name',
            'industry_slug',
            'domain_name',
            'logo',
            'hero_image',
            'primary_color',
            'secondary_color',
            'contact_email',
            'contact_phone',
            'address',
            'working_hours',
            'maps_url',
            'social_links',
            'custom_data',
            'status',
            'published_version',
            'created_at',
        ]


class ContactSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ['id', 'website', 'visitor_name', 'visitor_email', 'visitor_phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

