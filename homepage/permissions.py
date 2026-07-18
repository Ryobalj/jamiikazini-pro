# homepage/permissions.py

from rest_framework.permissions import BasePermission


class IsHomePageOwner(BasePermission):
    """
    Inaruhusu uandishi tu kwa mmiliki halisi wa Institution/Business
    iliyounganishwa na HomePage (au section husika, kupitia .homepage).
    """

    message = "Wewe si mmiliki wa homepage hii."

    def has_object_permission(self, request, view, obj):
        homepage = obj if hasattr(obj, 'is_owned_by') else getattr(obj, 'homepage', None)
        if homepage is None:
            parent = getattr(obj, 'about', None) or getattr(obj, 'what_we_do', None)
            homepage = getattr(parent, 'homepage', None)
        return bool(homepage and homepage.is_owned_by(request.user))
