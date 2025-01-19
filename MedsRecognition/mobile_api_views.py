from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import io
from PIL import Image

from MedsRecognition.auth_service import sign_in_user
from MedsRecognition.medication_serializer import MedicationSerializer
from MedsRecognition.medication_views import recognise
from rest_framework.pagination import PageNumberPagination
from MedsRecognition.models import Medication, Profile


class UserSignInView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        result = sign_in_user(email, password)

        if result and hasattr(result, "user"):
            # Ensure the profile exists
            Profile.objects.get_or_create(user_id=result.user.id, defaults={"display_name": email})
            token = result.session.access_token
            return Response({"token": token}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class UserSignOutView(APIView):
    def post(self, request):
        # Logic for invalidating user session or token
        return Response({"message": "Successfully signed out"}, status=status.HTTP_200_OK)


class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )


class MedicationsListView(APIView):
    def get(self, request):
        filter_param = request.query_params.get("filter", "")
        sort_param = request.query_params.get("sort", "id")

        medications = Medication.objects.filter(title__icontains=filter_param).order_by(sort_param)

        paginator = PageNumberPagination()
        paginated_medications = paginator.paginate_queryset(medications, request)

        serializer = MedicationSerializer(paginated_medications, many=True)
        return paginator.get_paginated_response(serializer.data)


class MedicationCreateView(APIView):
    def post(self, request):
        serializer = MedicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicationRecognizeView(APIView):
    def post(self, request):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response(
                {"error": "Image file not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = Image.open(io.BytesIO(image_file.read()))
            recognized_data = recognise(image)
            return Response(recognized_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
