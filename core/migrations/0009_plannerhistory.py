from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_alter_userquota_quota_bytes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlannerHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("start_auto", "Start Auto"),
                            ("option_select", "Option Select"),
                            ("user_input", "User Input"),
                            ("generate", "Generate"),
                            ("save", "Save"),
                        ],
                        max_length=32,
                    ),
                ),
                ("planner_step", models.CharField(blank=True, default="", max_length=64)),
                ("text", models.TextField(blank=True, default="")),
                ("option_id", models.IntegerField(blank=True, null=True)),
                ("option_label", models.CharField(blank=True, default="", max_length=255)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "session",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.chatsession"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="plannerhistory",
            index=models.Index(fields=["user", "session", "created_at"], name="core_planne_user_id_6eba0f_idx"),
        ),
        migrations.AddIndex(
            model_name="plannerhistory",
            index=models.Index(fields=["session", "created_at"], name="core_planne_session_dd5f95_idx"),
        ),
        migrations.AddIndex(
            model_name="plannerhistory",
            index=models.Index(fields=["event_type", "created_at"], name="core_planne_event_t_c56be5_idx"),
        ),
    ]
