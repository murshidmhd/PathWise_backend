# Generated migration — adds student_id and counselor_id as plain IntegerFields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatroom",
            name="student_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="chatroom",
            name="counselor_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]
