from django.contrib import admin
from django.contrib.auth import get_user_model
from kiini.admins import *

class JamiikaziniAdminSite(admin.AdminSite):
    site_header = "Jamiikazini Pro Admin"
    site_title = "Jamiikazini CEO Dashboard"
    index_title = "Muhtasari wa Mfumo"

    def each_context(self, request):
        context = super().each_context(request)

        # Start with user count
        dashboard_metrics = [
            {
                "title": "👥 Watumiaji",
                "value": get_user_model().objects.count(),
                "color": "#4285F4"
            }
        ]

        # Optional model imports
        model_map = {
            "🏢 Taasisi": ("kiini.models", "Institution", "#34A853"),
            "👔 Watumishi": ("institutions.models", "StaffProfile", "#0F9D58"),
            "📘 Shule": ("education.models", "School", "#FBBC05"),
            "📝 Lesson Plans": ("education.models", "LessonPlan", "#F4B400"),
            "📊 Scheme of Work": ("education.models", "SchemeOfWork", "#F29900"),
            "✅ Tasks": ("jamiitasks.models", "Task", "#EA4335"),
            "💰 Miamala": ("jamiiwallet.models", "Transaction", "#5F6368"),
            "🚚 Usafirishaji": ("logistics.models", "Delivery", "#AB47BC"),
            "🛂 Data ya Serikali": ("gov_integration.models", "GovData", "#00ACC1"),
            "💬 Ujumbe": ("jamiichat.models", "Message", "#6D4C41"),
            "🛡️ Login Events": ("security.models", "LoginHistory", "#455A64"),
            "💸 Malipo": ("payments.models", "Payment", "#00897B"),
        }

        for title, (module_path, model_name, color) in model_map.items():
            try:
                mod = __import__(module_path, fromlist=[model_name])
                model = getattr(mod, model_name)
                count = model.objects.count()
                dashboard_metrics.append({"title": title, "value": count, "color": color})
            except (ImportError, AttributeError):
                continue  # Skip if model not found or app not yet implemented

        context["dashboard_metrics"] = dashboard_metrics
        return context

# Instantiate admin site
jamiikazini_admin = JamiikaziniAdminSite(name='jamiikazini_admin')