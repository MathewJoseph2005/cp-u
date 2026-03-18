from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name="ImageRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_image_url", models.URLField()),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="analyzer.userprofile"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("health_score", models.IntegerField()),
                ("actions", models.JSONField()),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("overlay_image_url", models.URLField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "image",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="analyzer.imagerecord"),
                ),
            ],
        ),
    ]
