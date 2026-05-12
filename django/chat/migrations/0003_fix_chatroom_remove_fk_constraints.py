# Fixes the FK constraints that were accidentally created when
# on_delete=models.CASCADE was incorrectly added to IntegerField.
# This migration drops those constraints and ensures student_id and
# counselor_id are plain integer columns with no FK dependency.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_chatroom_counselor_id_chatroom_student_id"),
    ]

    operations = [
        # Remove and re-add student_id to strip any FK constraint
        migrations.RemoveField(
            model_name="chatroom",
            name="student_id",
        ),
        migrations.AddField(
            model_name="chatroom",
            name="student_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        # Remove and re-add counselor_id to strip any FK constraint
        migrations.RemoveField(
            model_name="chatroom",
            name="counselor_id",
        ),
        migrations.AddField(
            model_name="chatroom",
            name="counselor_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]
