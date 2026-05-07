from django.db import models

class UserProfile(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class ImageRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='images')
    original_image_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AnalysisResult(models.Model):
    image = models.ForeignKey(ImageRecord, on_delete=models.CASCADE, related_name='analysis')
    health_score = models.IntegerField()
    actions = models.JSONField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    overlay_image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
