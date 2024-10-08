# Generated by Django 4.2.13 on 2024-05-31 19:32

import django.core.validators
from django.db import migrations, models
import manies_maintenance_manager.jobs.validators


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0004_job_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="quote",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="quotes/",
                validators=[
                    django.core.validators.FileExtensionValidator(["pdf"]),
                    manies_maintenance_manager.jobs.validators.validate_pdf_contents,
                ],
            ),
        ),
    ]
