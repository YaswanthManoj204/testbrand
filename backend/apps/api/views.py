from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.domains.models import Domain
from apps.cards.models import BusinessCard
from apps.websites.models import Industry, Website, ContactSubmission
from .serializers import (
    DomainSerializer,
    DomainConnectSerializer,
    BusinessCardSerializer,
    BusinessCardPublicSerializer,
    IndustrySerializer,
    WebsiteSerializer,
    WebsitePublicSerializer,
    ContactSubmissionSerializer,
)


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer

    @action(detail=False, methods=['post'], url_path='connect')
    def connect_domain(self, request):
        """
        Registers a domain for verification and returns DNS challenge instructions.
        """
        serializer = DomainConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        domain_name = serializer.validated_data['domain_name']
        domain_type = serializer.validated_data['domain_type']

        domain, created = Domain.objects.get_or_create(
            domain_name=domain_name,
            defaults={'domain_type': domain_type}
        )

        return Response({
            'message': 'Domain registered. Configure the DNS TXT record to verify ownership.',
            'domain': DomainSerializer(domain).data,
            'dns_instructions': {
                'type': 'TXT',
                'host': domain.txt_record_name,
                'value': domain.verification_token,
                'a_record': {
                    'host': '@',
                    'ip': domain.target_ip
                },
                'cname_record': {
                    'host': 'www',
                    'target': domain.target_cname
                }
            }
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='verify')
    def verify_domain(self, request, pk=None):
        """
        Verifies DNS ownership (simulated/automated verification check).
        """
        domain = self.get_object()
        # In MVP/Dev environment, mark domain as verified and activate SSL
        domain.verification_status = 'verified'
        domain.ssl_status = 'active'
        domain.save()

        return Response({
            'success': True,
            'message': f'Domain {domain.domain_name} verified successfully. SSL is active.',
            'domain': DomainSerializer(domain).data
        })


class IndustryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Industry.objects.filter(is_active=True)
    serializer_class = IndustrySerializer
    lookup_field = 'slug'


class BusinessCardViewSet(viewsets.ModelViewSet):
    queryset = BusinessCard.objects.all()
    serializer_class = BusinessCardSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return BusinessCard.objects.filter(user=user)
        return BusinessCard.objects.all()

    @action(detail=False, methods=['get'], url_path='public/(?P<identifier>[^/.]+)')
    def public_card(self, request, identifier=None):
        """
        Public endpoint used by pre-made business card template engine.
        Accepts card_id, slug, or connected domain.
        """
        card = BusinessCard.objects.filter(
            card_id__iexact=identifier
        ).first() or BusinessCard.objects.filter(
            slug__iexact=identifier
        ).first() or BusinessCard.objects.filter(
            domain__domain_name__iexact=identifier
        ).first()

        if not card:
            return Response({'error': 'Business card not found'}, status=status.HTTP_404_NOT_FOUND)

        # Increment view count
        BusinessCard.objects.filter(pk=card.pk).update(views_count=card.views_count + 1)
        card.refresh_from_db()

        serializer = BusinessCardPublicSerializer(card, context={'request': request})
        return Response(serializer.data)


class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Website.objects.filter(user=user)
        return Website.objects.all()

    @action(detail=False, methods=['get'], url_path='public/(?P<identifier>[^/.]+)')
    def public_website(self, request, identifier=None):
        """
        Public endpoint consumed by the PHP website engine or frontend previews.
        Accepts site_id, slug, or connected domain.
        """
        website = Website.objects.filter(
            site_id__iexact=identifier
        ).first() or Website.objects.filter(
            slug__iexact=identifier
        ).first() or Website.objects.filter(
            domain__domain_name__iexact=identifier
        ).first()

        if not website:
            return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)

        # Increment view count
        Website.objects.filter(pk=website.pk).update(views_count=website.views_count + 1)
        website.refresh_from_db()

        serializer = WebsitePublicSerializer(website, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='enquiries')
    def submit_enquiry(self, request, pk=None):
        """
        Allows visitors to submit a contact inquiry to this specific website.
        """
        website = self.get_object()
        data = request.data.copy()
        data['website'] = website.id

        serializer = ContactSubmissionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': 'Your message has been sent successfully.',
            'enquiry': serializer.data
        }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def platform_health(request):
    """
    Health check and platform stats endpoint.
    """
    return Response({
        'status': 'healthy',
        'platform': 'BrandNest Digital Presence Engine',
        'version': '1.0.0',
        'stats': {
            'industries': Industry.objects.count(),
            'business_cards': BusinessCard.objects.count(),
            'websites': Website.objects.count(),
            'domains': Domain.objects.count(),
        }
    })
