# kiini/menu_config.py

from typing import List, Dict, Union

MENU_CONFIG: List[Dict[str, Union[str, List[str], None]]] = [
    {
        "label": "Jamii Center",
        "i18nKey": "tabs.kiini_dashboard",
        "icon": "LayoutDashboard",
        "url": "/kiini/dashboard/",
        "app": "kiini",
        "roles": ["ADMIN", "INSTITUTION_ADMIN", "CLIENT", "PROVIDER"],
        "domain": None,
    },

    {
        "label": "Business Hub",
        "i18nKey": "tabs.business_dashboard",
        "icon": "Briefcase",
        "url": "/businesses/dashboard/{business_id}/",
        "app": "businesses",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "Learning Space",
        "i18nKey": "tabs.education_dashboard",
        "icon": "GraduationCap",
        "url": "/education/dashboard/",
        "app": "education",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "Government Services",
        "i18nKey": "tabs.gov_dashboard",
        "icon": "Gavel",
        "url": "/gov_integration/dashboard/",
        "app": "gov_integration",
        "roles": ["ADMIN"],
        "domain": None,
    },

    {
        "label": "Health Center",
        "i18nKey": "tabs.health_dashboard",
        "icon": "HeartPulse",
        "url": "/health/dashboard/",
        "app": "health",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "Connect Chat",
        "i18nKey": "tabs.chat_dashboard",
        "icon": "MessageSquare",
        "url": "/jamiichat/dashboard/",
        "app": "jamiichat",
        "roles": ["CLIENT", "PROVIDER", "ADMIN", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "My Wallet",
        "i18nKey": "tabs.wallet_dashboard",
        "icon": "Wallet",
        "url": "/jamiiwallet/dashboard/",
        "app": "jamiiwallet",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "Logistics Hub",
        "i18nKey": "tabs.logistics_dashboard",
        "icon": "Truck",
        "url": "/logistics/dashboard/",
        "app": "logistics",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "Payments Center",
        "i18nKey": "tabs.payments_dashboard",
        "icon": "CreditCard",
        "url": "/payments/dashboard/",
        "app": "payments",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "Search Center",
        "i18nKey": "tabs.search_dashboard",
        "icon": "Search",
        "url": "/search/dashboard/",
        "app": "search",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

    {
        "label": "My Portfolio",
        "i18nKey": "tabs.portfolio_dashboard",
        "icon": "FolderKanban",
        "url": "/portfolio/",
        "app": "portfolio",
        "roles": ["CLIENT", "PROVIDER", "INSTITUTION_ADMIN"],
        "domain": None,
    },

]

