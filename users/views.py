from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import serializers, status
from .serializers import RegisterSerializer
from drf_spectacular.utils import extend_schema


class RegisterView(APIView):
    @extend_schema(request=RegisterSerializer)
    def post(self, request):
        serilaizer = RegisterSerializer(data=request.data)

        if serilaizer.is_valid():
            serilaizer.save()

            return Response(
                {"message": "User registerd successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serilaizer.errors, status=status.HTTP_400_BAD_REQUEST)
