from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# Import all views from views_mongo_new for backwards compatibility
from .views_mongo_new import (
    RegisterView,
    LoginView, 
    AnalyzeView,
    AnalyzeBatchView,
    ResultsView,
    ReportTTSView,
)

# Alias for backwards compatibility
GetAnalysisResultsView = ResultsView
