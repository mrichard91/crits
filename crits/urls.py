from django.conf import settings
from django.urls import include, re_path as url

urlpatterns = [

    url(r'^', include('crits.core.urls')),                        # Core
    url(r'^dashboards/', include('crits.dashboards.urls')),       # Dashboard
    url(r'^actors/', include('crits.actors.urls')),               # Actors
    url(r'^backdoors/', include('crits.backdoors.urls')),         # Backdoors
    url(r'^campaigns/', include('crits.campaigns.urls')),         # Campaigns
    url(r'^certificates/', include('crits.certificates.urls')),   # Certificates
    url(r'^comments/', include('crits.comments.urls')),           # Comments
    url(r'^domains/', include('crits.domains.urls')),             # Domains
    url(r'^emails/', include('crits.emails.urls')),               # Emails
    url(r'^events/', include('crits.events.urls')),               # Events
    url(r'^exploits/', include('crits.exploits.urls')),           # Exploits
    url(r'^indicators/', include('crits.indicators.urls')),       # Indicators
    url(r'^ips/', include('crits.ips.urls')),                     # IPs
    url(r'^locations/', include('crits.locations.urls')),         # Locations
    url(r'^notifications/', include('crits.notifications.urls')), # Notifications
    url(r'^objects/', include('crits.objects.urls')),             # Objects
    url(r'^pcaps/', include('crits.pcaps.urls')),                 # PCAPs
    url(r'^raw_data/', include('crits.raw_data.urls')),           # Raw Data
    url(r'^relationships/', include('crits.relationships.urls')), # Relationships
    url(r'^samples/', include('crits.samples.urls')),             # Samples
    url(r'^screenshots/', include('crits.screenshots.urls')),     # Screenshots
    url(r'^services/', include('crits.services.urls')),           # Services
    url(r'^signatures/', include('crits.signatures.urls')),       # Signatures
    url(r'^targets/', include('crits.targets.urls')),             # Targets
]

# Error overrides
handler500 = 'crits.core.errors.custom_500'
handler404 = 'crits.core.errors.custom_404'
handler403 = 'crits.core.errors.custom_403'
handler400 = 'crits.core.errors.custom_400'

# This code allows static content to be served up by the development server
if settings.DEVEL_INSTANCE:
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns.append(
            url(r'^%s(?P<path>.*)$' % _media_url, serve, {'document_root': settings.MEDIA_ROOT}))
    del(_media_url, serve)

if settings.ENABLE_DT:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
