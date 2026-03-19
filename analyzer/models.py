from django.db import models


class UserProfile(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=128, null=True, blank=True)


class ImageRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="images")
    original_image_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


class AnalysisResult(models.Model):
    image = models.ForeignKey(ImageRecord, on_delete=models.CASCADE, related_name="results")
    health_score = models.IntegerField()
    actions = models.JSONField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    camera_number = models.IntegerField(null=True, blank=True)
    field_zone = models.CharField(max_length=128, null=True, blank=True)
    overlay_image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
