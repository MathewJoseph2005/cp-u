from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
<<<<<<< HEAD
from .serializers import AnalyzeInputSerializer, AnalysisResultSerializer
from .services import analyze_image

class AnalyzeView(APIView):
    def post(self, request):
        serializer = AnalyzeInputSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = analyze_image(serializer.validated_data)
                output_serializer = AnalysisResultSerializer(result)
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "Internal server error during analysis."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
=======
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
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
