from django.db import migrations


def mark_default_accounts(apps, schema_editor):
    Account = apps.get_model("finance", "account")
    Account.objects.filter(type__in=("CC", "DN")).update(
        include_in_emergency_reserve=True,
        include_in_liquidity=True,
    )


def unmark_default_accounts(apps, schema_editor):
    Account = apps.get_model("finance", "account")
    Account.objects.filter(type__in=("CC", "DN")).update(
        include_in_emergency_reserve=False,
        include_in_liquidity=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0012_add_reserve_and_liquidity_fields"),
    ]

    operations = [
        migrations.RunPython(mark_default_accounts, unmark_default_accounts),
    ]
