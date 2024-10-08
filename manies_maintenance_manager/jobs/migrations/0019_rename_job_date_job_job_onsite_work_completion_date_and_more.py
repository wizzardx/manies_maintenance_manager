# Generated by Django 5.0.7 on 2024-08-04 10:47

import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0018_alter_job_status"),
    ]

    operations = [
        migrations.RenameField(
            model_name="job",
            old_name="job_date",
            new_name="job_onsite_work_completion_date",
        ),
        migrations.AlterField(
            model_name="job",
            name="job_onsite_work_completion_date",
            field=models.DateField(
                blank=True,
                help_text="Date when onsite work was completed.",
                null=True,
                verbose_name="Job Date",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="status",
            field=model_utils.fields.StatusField(
                choices=[
                    ("pending_inspection", "Pending Inspection"),
                    ("inspection_completed", "Inspection Completed"),
                    ("quote_uploaded", "Quote Uploaded"),
                    ("quote_rejected_by_agent", "Quote Rejected By Agent"),
                    ("quote_accepted_by_agent", "Quote Accepted By Agent"),
                    ("deposit_pop_uploaded", "Deposit POP Uploaded"),
                    (
                        "manie_completed_onsite_work",
                        "Manie has completed the onsite work",
                    ),
                    (
                        "manie_submitted_documentation",
                        "Manie submitted final documentation",
                    ),
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
