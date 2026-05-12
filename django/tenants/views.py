from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connection
from .models import Organization
from .serializers import OrganizationSerializer, CreateCollegeAdminSerializer
from accounts.models import User

class IsPlatformAdmin(permissions.BasePermission):
    message = "Only platform admins can access this endpoint."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "platform_admin")

class OrganizationListView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        # Exclude the public schema itself
        organizations = Organization.objects.exclude(schema_name='public')
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data)

class CreateCollegeAdminView(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request):
        serializer = CreateCollegeAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        org_id = serializer.validated_data['organization_id']
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # IMPORTANT: Switch to the tenant schema to create the user there
        connection.set_tenant(organization)
        
        try:
            # Check if user already exists in this tenant
            if User.objects.filter(email=serializer.validated_data['email']).exists():
                return Response({"error": "User already exists in this college"}, status=status.HTTP_400_BAD_REQUEST)

            # Create the college admin user
            User.objects.create_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                role='college_admin',
                is_staff=True,  # Allow access to college's django admin
                is_active=True,
                is_verified=True,
                is_approved=True
            )
            return Response({
                "message": f"College Admin created successfully for {organization.name}"
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            # Always switch back to public schema to avoid affecting other requests
            connection.set_schema_to_public()

class CreateOrganizationView(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request):
        from .models import Domain
        from .serializers import CreateOrganizationSerializer
        
        serializer = CreateOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # 1. Create Organization (triggers schema creation)
            org = Organization.objects.create(
                name=serializer.validated_data['name'],
                schema_name=serializer.validated_data['schema_name'],
                plan=serializer.validated_data.get('plan', 'free')
            )
            
            # 2. Create Domain
            Domain.objects.create(
                domain=serializer.validated_data['domain_name'],
                tenant=org,
                is_primary=True
            )
            
            return Response({
                "message": f"Organization '{org.name}' created successfully with schema '{org.schema_name}'",
                "organization": {
                    "id": org.id,
                    "name": org.name,
                    "schema_name": org.schema_name,
                    "domain": serializer.validated_data['domain_name']
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
