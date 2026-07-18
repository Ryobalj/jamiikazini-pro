# accounts/migrations/0005_backfill_national_id_hash.py
#
# Backfill ya national_id_hash kwa watumiaji waliokwishathibitishwa kabla ya
# kizuizi cha "NIDA/NIN moja = akaunti moja" kuwekwa. Kama watumiaji wawili
# wa zamani wanashiriki NIN ileile (data chafu ya kabla ya kizuizi), wa kwanza
# (aliyeundwa mapema) anabaki na hash; wengine wanaachwa NULL ili migration
# isivunjike - watashughulikiwa kimkono na admin.

from django.db import migrations


def backfill_hashes(apps, schema_editor):
    # Helpers hazitegemei model state - salama kuzitumia moja kwa moja.
    from security.helpers.encryption import decrypt_data, hash_data

    User = apps.get_model("accounts", "User")
    seen = set()
    for user in User.objects.exclude(_national_id__isnull=True).exclude(_national_id="").order_by("created_at"):
        try:
            plain = decrypt_data(user._national_id)
        except Exception:
            # Ciphertext isiyosomeka (key ya zamani/iliyoharibika) - ruka.
            continue
        nid_hash = hash_data(plain)
        if nid_hash in seen:
            continue
        seen.add(nid_hash)
        User.objects.filter(pk=user.pk).update(national_id_hash=nid_hash)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_national_id_hash"),
    ]

    operations = [
        migrations.RunPython(backfill_hashes, noop),
    ]
