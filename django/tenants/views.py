import uuid
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import connection
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Organization, Domain
from .serializers import OrganizationSerializer, InviteCollegeAdminSerializer, SetupAccountSerializer
from accounts.models import User

class IsPlatformAdmin(permissions.BasePermission):
    message = "Only platform admins can access this endpoint."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "platform_admin")

class OrganizationListView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        organizations = Organization.objects.exclude(schema_name='public')
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data)

class InviteCollegeAdminView(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request):
        serializer = InviteCollegeAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        org_id = serializer.validated_data['organization_id']
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Switch to tenant schema
        connection.set_tenant(organization)
        
        try:
            email = serializer.validated_data['email']
            if User.objects.filter(email=email).exists():
                return Response({"error": "User already exists in this college"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate invite token
            token = str(uuid.uuid4())
            
            # Create inactive user with token
            User.objects.create(
                email=email,
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                role='college_admin',
                is_staff=True,
                is_active=False, # Inactive until password set
                is_verified=True,
                is_approved=True,
                invitation_token=token,
                invitation_created_at=timezone.now()
            )
            
            # Generate the setup URL (in real app, this goes in the email)
            # Using a relative path or a known frontend domain
            setup_url = f"/auth/setup-account/{token}"

            return Response({
                "message": f"Invitation created for {email}",
                "setup_url": setup_url,
                "token": token
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            connection.set_schema_to_public()

class SetupAccountView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SetupAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        # We need to find the user across all schemas? 
        # Actually, in django-tenants, users can be in the public schema OR tenant schema.
        # If the user is a college_admin, they are likely in a tenant schema.
        # For simplicity, we can ask for the 'domain' or just search all tenants.
        # But a better way is to put 'global' users in Public.
        
        # Let's search all organizations for this token
        orgs = Organization.objects.exclude(schema_name='public')
        for org in orgs:
            connection.set_tenant(org)
            user = User.objects.filter(invitation_token=token).first()
            if user:
                # Found him!
                user.set_password(password)
                user.invitation_token = None # Clear token
                user.is_active = True
                user.save()
                connection.set_schema_to_public()
                return Response({"message": "Account setup successful. You can now login."}, status=status.HTTP_200_OK)
        
        connection.set_schema_to_public()
        return Response({"error": "Invalid or expired invitation token"}, status=status.HTTP_400_BAD_REQUEST)

class ToggleOrganizationStatusView(APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        organization.is_active = not organization.is_active
        organization.save()
        
        status_str = "activated" if organization.is_active else "deactivated"
        return Response({"message": f"Organization {organization.name} has been {status_str}."})

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
