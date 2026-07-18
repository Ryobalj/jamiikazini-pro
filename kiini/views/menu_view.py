# kiini/views/menu_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging

from businesses.models import Business
from kiini.models.institution import Institution

logger = logging.getLogger(__name__)


def get_user_capabilities(user):
    """Single source of truth for the ownership/verification signals both
    UserMenuView and DashboardContextView need, so they can't drift apart."""
    business = Business.objects.filter(owner=user).first()
    has_transport_provider = user.transport_providers.exists()
    verification = getattr(user, "transport_verification", None)
    return {
        "is_identity_verified": bool(getattr(user, "is_identity_verified", False)),
        "business": business,
        "has_transport_provider": has_transport_provider,
        "driver_verification_status": verification.overall_status if verification else None,
    }


class UserMenuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        caps = get_user_capabilities(user)
        visible_menu = []

        # 📍 Always: Nearby Businesses (first)
        visible_menu.append({
            "app": "nearby",
            "i18nKey": "nearby.title",
            "icon": "MapPin",
            "url": "/nearby",
        })

        # ⚠️ Prominent verification prompt if not identity-verified yet
        if not caps["is_identity_verified"]:
            visible_menu.append({
                "app": "verification",
                "i18nKey": "verification.required",
                "icon": "ShieldAlert",
                "url": "/verify-identity",
            })

        # 💰 JamiiWallet
        visible_menu.append({
            "app": "wallet",
            "i18nKey": "wallet.title",
            "icon": "Wallet",
            "url": "/jamiiwallet",
        })

        # 🛒 Cart
        visible_menu.append({
            "app": "cart",
            "i18nKey": "cart.title",
            "icon": "ShoppingCart",
            "url": "/cart",
        })

        # 📦 My Orders
        visible_menu.append({
            "app": "orders",
            "i18nKey": "orders.title",
            "icon": "Package",
            "url": "/orders",
        })

        # 🚚 Request a delivery/pickup (standalone - no product purchase behind it)
        visible_menu.append({
            "app": "request_service",
            "i18nKey": "request_service.title",
            "icon": "Truck",
            "url": "/logistics/request",
        })

        # 🌍 Import sourcing - omba bidhaa iagizwe kutoka nje ya nchi
        visible_menu.append({
            "app": "request_import",
            "i18nKey": "import_requests.title",
            "icon": "Globe",
            "url": "/request-import",
        })

        # ⚡ Malipo ya huduma (LUKU, airtime, DSTV, maji)
        visible_menu.append({
            "app": "billpay",
            "i18nKey": "billpay.title",
            "icon": "Zap",
            "url": "/billpay",
        })

        # 🏠 Mali isiyohamishika (nyumba/viwanja)
        visible_menu.append({
            "app": "realestate",
            "i18nKey": "realestate.title",
            "icon": "Home",
            "url": "/realestate",
        })

        # 🌾 Mikataba ya awali ya mazao (bei kwa uzito halisi)
        visible_menu.append({
            "app": "request_harvest",
            "i18nKey": "agriculture.title",
            "icon": "Wheat",
            "url": "/request-harvest",
        })

        # 👷 Miradi ya ujenzi/kandarasi (malipo ya awamu)
        visible_menu.append({
            "app": "request_project",
            "i18nKey": "construction.title",
            "icon": "HardHat",
            "url": "/request-project",
        })

        # 🤝 VICOBA/SACCOS - vikundi vya akiba ya pamoja
        visible_menu.append({
            "app": "savings",
            "i18nKey": "savings.title",
            "icon": "Users",
            "url": "/savings",
        })

        # 💬 Jamiichat
        visible_menu.append({
            "app": "chat",
            "i18nKey": "chat.title",
            "icon": "MessageCircle",
            "url": "/jamiichat",
        })

        # 🏪 My Business - dashboard submenu if owned, else a register link
        try:
            business = caps["business"]
            if business:
                business_menu = {
                    "app": "business",
                    "i18nKey": "business.dashboard",
                    "icon": "Store",
                    "sub": [
                        {
                            "i18nKey": "dashboard.overview",
                            "url": f"/businesses/dashboard/{business.id}/overview",
                            "icon": "LayoutDashboard",
                        },
                        {
                            "i18nKey": "dashboard.products",
                            "url": f"/businesses/dashboard/{business.id}/products",
                            "icon": "Package",
                        },
                        {
                            "i18nKey": "dashboard.services",
                            "url": f"/businesses/dashboard/{business.id}/services",
                            "icon": "Wrench",
                        },
                        {
                            "i18nKey": "dashboard.branches",
                            "url": f"/businesses/dashboard/{business.id}/branches",
                            "icon": "Building2",
                        },
                        {
                            "i18nKey": "dashboard.settings",
                            "url": f"/businesses/dashboard/{business.id}/settings",
                            "icon": "Settings",
                        },
                        {
                            "i18nKey": "dashboard.credit_account",
                            "url": "/businesses/credit-account",
                            "icon": "CreditCard",
                        },
                        {
                            "i18nKey": "dashboard.offers",
                            "url": f"/businesses/dashboard/{business.id}/offers",
                            "icon": "Tag",
                        },
                        {
                            "i18nKey": "dashboard.import_requests",
                            "url": f"/businesses/dashboard/{business.id}/imports",
                            "icon": "Globe",
                        },
                        {
                            "i18nKey": "dashboard.harvest",
                            "url": f"/businesses/dashboard/{business.id}/harvest",
                            "icon": "Wheat",
                        },
                        {
                            "i18nKey": "dashboard.tenders",
                            "url": f"/businesses/dashboard/{business.id}/tenders",
                            "icon": "HardHat",
                        },
                    ],
                }
            else:
                business_menu = {
                    "app": "business",
                    "i18nKey": "business.register",
                    "url": "/businesses/register/",
                    "icon": "PlusCircle"
                }
            visible_menu.append(business_menu)
        except Exception as e:
            logger.warning(f"⚠️ Failed to append business menu for user {user.email}: {e}")

        # 🚚 Driver - jobs/deliveries/verification submenu if registered, else a register link
        try:
            if caps["has_transport_provider"]:
                driver_menu = {
                    "app": "driver",
                    "i18nKey": "driver.dashboard",
                    "icon": "Truck",
                    "sub": [
                        {
                            "i18nKey": "driver.jobs",
                            "url": "/logistics/jobs",
                            "icon": "Package",
                        },
                        {
                            "i18nKey": "driver.deliveries",
                            "url": "/logistics/deliveries",
                            "icon": "Truck",
                        },
                        {
                            "i18nKey": "driver.verify",
                            "url": "/logistics/verify",
                            "icon": "ShieldCheck",
                        },
                    ],
                }
            else:
                driver_menu = {
                    "app": "driver",
                    "i18nKey": "driver.register",
                    "url": "/logistics/jobs",
                    "icon": "Truck",
                }
            visible_menu.append(driver_menu)
        except Exception as e:
            logger.warning(f"⚠️ Failed to append driver menu for user {user.email}: {e}")

        # 🏛️ My Institutions - unchanged
        try:
            institutions = Institution.objects.filter(owner=user)

            if institutions.exists():
                institution_menu = {
                    "app": "institutions",
                    "i18nKey": "institutions.title",
                    "icon": "Building2",
                    "sub": []
                }

                for inst in institutions[:5]:
                    institution_menu["sub"].append({
                        "i18nKey": None,
                        "label": inst.name,
                        "url": f"/kiini/institutions/{inst.id}",
                        "icon": "Building",
                    })

                institution_menu["sub"].append({
                    "i18nKey": "institutions.create_new",
                    "url": "/institutions/create",
                    "icon": "Plus",
                })

                visible_menu.append(institution_menu)
            else:
                visible_menu.append({
                    "app": "institutions",
                    "i18nKey": "institutions.create",
                    "url": "/institutions/create",
                    "icon": "PlusCircle"
                })

        except Exception as e:
            logger.warning(f"⚠️ Failed to append institutions menu for user {user.email}: {e}")

        return Response(visible_menu, status=status.HTTP_200_OK)


class DashboardContextView(APIView):
    """Extra ownership/verification signals the Home quick-actions dashboard
    needs but the menu array can't carry (it must stay a flat list of links
    for Sidebar.jsx). Reuses the exact same lookups as UserMenuView via
    get_user_capabilities() so the two can never disagree."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        caps = get_user_capabilities(request.user)
        business = caps["business"]
        business_data = None
        if business:
            credit_account = getattr(business, "credit_account", None)
            business_data = {
                "id": business.id,
                "name": business.name,
                "is_verified": business.is_verified,
                "credit_limit": str(credit_account.credit_limit) if credit_account else "0.00",
                "available_credit": str(credit_account.available_credit) if credit_account else "0.00",
            }
        return Response({
            "is_identity_verified": caps["is_identity_verified"],
            "business": business_data,
            "driver": {
                "has_vehicle_provider": caps["has_transport_provider"],
                "verification_status": caps["driver_verification_status"],
            } if caps["has_transport_provider"] else None,
        }, status=status.HTTP_200_OK)
