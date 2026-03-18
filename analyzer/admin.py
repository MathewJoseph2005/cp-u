from django.contrib import admin

from .models import AnalysisResult, ImageRecord, UserProfile

admin.site.register(UserProfile)
admin.site.register(ImageRecord)
admin.site.register(AnalysisResult)
