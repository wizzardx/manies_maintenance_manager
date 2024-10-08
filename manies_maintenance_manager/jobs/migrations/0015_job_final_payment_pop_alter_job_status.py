# Generated by Django 4.2.13 on 2024-06-26 13:12

import django.core.validators
from django.db import migrations, models
import manies_maintenance_manager.jobs.validators
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0014_job_complete"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="final_payment_pop",
            field=models.FileField(
                blank=True,
                help_text="Upload the final payment proof of payment here.",
                null=True,
                upload_to="final_payment_pops/",
                validators=[
                    django.core.validators.FileExtensionValidator(["pdf"]),
                    manies_maintenance_manager.jobs.validators.validate_pdf_contents,
                ],
                verbose_name="Final Payment Proof of Payment",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="status",
            field=model_utils.fields.StatusField(
                choices=[
                    ("pending_inspection", "Pending Inspection"),
                    ("inspection_completed", "Inspection Completed"),
                    ("quote_rejected_by_agent", "Quote Rejected By Agent"),
                    ("quote_accepted_by_agent", "Quote Accepted By Agent"),
                    ("deposit_pop_uploaded", "Deposit POP Uploaded"),
                    ("manie_completed", "Manie has completed the job"),
                    (
                        "final_payment_pop_uploaded",
                        "Agent uploaded the final payment POP",
                    ),
                ],
                default="pending_inspection",
                max_length=100,
                no_check_for_status=True,
            ),
        ),
    ]
