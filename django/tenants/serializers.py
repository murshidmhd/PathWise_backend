from rest_framework import serializers
from .models import Organization, Domain
from accounts.models import User

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary']

class OrganizationSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'schema_name', 'plan', 'created_at', 'domains']

class InviteCollegeAdminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    organization_id = serializers.IntegerField()

class SetupAccountSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)

class CreateOrganizationSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(write_only=True)

    class Meta:
        model = Organization
        fields = ['name', 'schema_name', 'plan', 'domain_name']

    def validate_schema_name(self, value):
        if Organization.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError("Schema name already exists.")
        return value.lower().replace(' ', '_')
