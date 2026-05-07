<<<<<<< HEAD
=======
from django.conf import settings
from django.conf.urls.static import static
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("analyzer.urls")),
]
<<<<<<< HEAD
=======

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
