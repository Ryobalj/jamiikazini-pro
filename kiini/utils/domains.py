def get_subdomain(request):
    host = request.get_host().split(':')[0]
    domain_parts = host.split('.')

    if len(domain_parts) > 2:
        return domain_parts[0]  # e.g. shule1.jamiikazini.com -> shule1
    return None