# Generated by Django 5.0.8 on 2024-08-06 20:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="is_marnie",
            new_name="is_manie",
        ),
    ]
