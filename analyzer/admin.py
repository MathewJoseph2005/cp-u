from django.contrib import admin

<<<<<<< HEAD
from .models import AnalysisResult

=======
from .models import AnalysisResult, ImageRecord, UserProfile

admin.site.register(UserProfile)
admin.site.register(ImageRecord)
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
admin.site.register(AnalysisResult)
