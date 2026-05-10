# kiini/views/menu_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import logging

from businesses.models import Business
from kiini.models.institution import Institution

logger = logging.getLogger(__name__)

class UserMenuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_roles = getattr(user, 'roles', []) or []
        
        # Simplified menu - only 3 items
        visible_menu = []

        # 📍 1. NEARBY - Dynamic (always first)
        try:
            nearby_menu = {
                "app": "nearby",
                "i18nKey": "nearby.title",
                "icon": "MapPin",
                "url": "/nearby",
            }
            visible_menu.append(nearby_menu)
            logger.info(f"✅ Nearby menu added for user {user.email}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to append nearby menu for user {user.email}: {e}")

        # 🏪 2. MY BUSINESSES - Dynamic based on user's businesses
        try:
            business = Business.objects.filter(owner=user).first()
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
                    ],
                }
                logger.info(f"✅ Business dashboard menu added for user {user.email}")
            else:
                business_menu = {
                    "app": "business",
                    "i18nKey": "business.register",
                    "url": "/businesses/register/",
                    "icon": "PlusCircle"
                }
                logger.info(f"✅ Business register menu added for user {user.email}")
            
            visible_menu.append(business_menu)
        except Exception as e:
            logger.warning(f"⚠️ Failed to append business menu for user {user.email}: {e}")

        # 🏛️ 3. MY INSTITUTIONS - Dynamic based on user's institutions
        try:
            institutions = Institution.objects.filter(owner=user)
            
            if institutions.exists():
                # User has institutions - show them as submenu
                institution_menu = {
                    "app": "institutions",
                    "i18nKey": "institutions.title",
                    "icon": "Building2",
                    "sub": []
                }
                
                for inst in institutions[:5]:  # Limit to 5 institutions
                    institution_menu["sub"].append({
                        "i18nKey": None,
                        "label": inst.name,
                        "url": f"/kiini/institutions/{inst.id}",
                        "icon": "Building",
                    })
                
                # Add "Create New" option
                institution_menu["sub"].append({
                    "i18nKey": "institutions.create_new",
                    "url": "/institutions/create",
                    "icon": "Plus",
                })
                
                visible_menu.append(institution_menu)
                logger.info(f"✅ Institutions menu added for user {user.email} ({institutions.count()} institutions)")
            else:
                # No institutions - show create button
                institution_menu = {
                    "app": "institutions",
                    "i18nKey": "institutions.create",
                    "url": "/institutions/create",
                    "icon": "PlusCircle"
                }
                visible_menu.append(institution_menu)
                logger.info(f"✅ Create institution menu added for user {user.email}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to append institutions menu for user {user.email}: {e}")

        return Response(visible_menu, status=status.HTTP_200_OK)