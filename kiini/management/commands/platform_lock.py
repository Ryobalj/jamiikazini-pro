# kiini/management/commands/platform_lock.py
#
# Second way to flip the platform lock, for when /admin/ isn't handy (e.g.
# a Render shell session). Usage:
#   python manage.py platform_lock status
#   python manage.py platform_lock on --message "Custom notice..."
#   python manage.py platform_lock off

from django.core.management.base import BaseCommand
from kiini.models.platform_lock import PlatformLock


class Command(BaseCommand):
    help = "Check or flip the site-wide platform lock (locks everything except JamiiShule for non-admins)."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["on", "off", "status"])
        parser.add_argument("--message", default=None, help="Custom notice shown to locked-out users (only used with 'on').")

    def handle(self, *args, **options):
        obj, _ = PlatformLock.objects.get_or_create(pk=1)

        if options["action"] == "status":
            state = "LOCKED" if obj.is_locked else "unlocked"
            self.stdout.write(self.style.SUCCESS(f"Platform is currently {state}."))
            if obj.is_locked and obj.message:
                self.stdout.write(f"Message: {obj.message}")
            return

        obj.is_locked = options["action"] == "on"
        if options["action"] == "on" and options["message"] is not None:
            obj.message = options["message"]
        obj.save()

        state = "LOCKED" if obj.is_locked else "unlocked"
        self.stdout.write(self.style.SUCCESS(f"Platform is now {state}."))
