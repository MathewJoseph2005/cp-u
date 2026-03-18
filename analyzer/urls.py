from django.urls import path

from .views import AnalyzeView, LoginView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("analyze/", AnalyzeView.as_view(), name="analyze"),
]
