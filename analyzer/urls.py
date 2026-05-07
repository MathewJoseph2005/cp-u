from django.urls import path
<<<<<<< HEAD

from .views import AnalyzeAPIView

urlpatterns = [
    path("analyze/", AnalyzeAPIView.as_view(), name="analyze"),
=======
from .views import AnalyzeView, AnalyzeBatchView, RegisterView, LoginView, ResultsView, ReportTTSView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("analyze/", AnalyzeView.as_view(), name="analyze"),
    path("analyze/batch/", AnalyzeBatchView.as_view(), name="analyze-batch"),
    path("results/", ResultsView.as_view(), name="results"),
    path("tts/report/", ReportTTSView.as_view(), name="tts-report"),
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
]
