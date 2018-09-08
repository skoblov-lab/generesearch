from django.conf import settings


def google_analytics(request):
    """
    Use the variables returned in this function to
    render your Google Analytics tracking code template.
    """
    ga_prop_id = getattr(settings, 'GOOGLE_ANALYTICS_PROPERTY_ID', None)
    ga_domain = getattr(settings, 'GOOGLE_ANALYTICS_DOMAIN', None)
    return (
        {} if settings.DEBUG or not all([ga_prop_id, ga_domain]) else
        {'GOOGLE_ANALYTICS_PROPERTY_ID': ga_prop_id,
         'GOOGLE_ANALYTICS_DOMAIN': ga_domain}
    )