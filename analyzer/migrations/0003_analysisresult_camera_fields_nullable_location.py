from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyzer", "0002_userprofile_password_alter_userprofile_phone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="analysisresult",
            name="latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="analysisresult",
            name="longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="analysisresult",
            name="camera_number",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="analysisresult",
            name="field_zone",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
