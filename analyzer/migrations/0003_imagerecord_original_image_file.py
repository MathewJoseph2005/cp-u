from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyzer", "0002_userprofile_password_alter_userprofile_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="imagerecord",
            name="original_image_file",
            field=models.ImageField(blank=True, null=True, upload_to="uploaded_images/%Y/%m/%d/"),
        ),
    ]
