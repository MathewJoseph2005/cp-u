from django.urls import path
from .views import AnalyzeView, AnalyzeBatchView, RegisterView, LoginView, ResultsView, ReportTTSView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("analyze/", AnalyzeView.as_view(), name="analyze"),
    path("analyze/batch/", AnalyzeBatchView.as_view(), name="analyze-batch"),
    path("results/", ResultsView.as_view(), name="results"),
    path("tts/report/", ReportTTSView.as_view(), name="tts-report"),
]
