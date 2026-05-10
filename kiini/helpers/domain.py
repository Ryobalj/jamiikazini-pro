# kiini/helpers/domain.py

def generate_subdomain_url(domain: str, path: str = "") -> str:
    """
    Generate full URL based on a full domain and optional path.

    Example:
        generate_subdomain_url("school1.jamiikazini.com", "/dashboard/")
        -> https://school1.jamiikazini.com/dashboard/
    """
    path = path.lstrip("/")
    return f"https://{domain}/{path}" if path else f"https://{domain}"


def get_subdomain_from_host(host):
    """
    Extracts subdomain from host like shule1.jamiikazini.com
    """
    parts = host.split('.')
    if len(parts) >= 3:
        return parts[0]  # e.g., 'shule1'
    return None