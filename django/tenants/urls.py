from .views import (
    OrganizationListView, 
    InviteCollegeAdminView, 
    CreateOrganizationView,
    SetupAccountView,
    ToggleOrganizationStatusView
)
from django.urls import path

urlpatterns = [
    path('organizations/', OrganizationListView.as_view(), name='organization-list'),
    path('organizations/create/', CreateOrganizationView.as_view(), name='create-organization'),
    path('organizations/<int:pk>/toggle-status/', ToggleOrganizationStatusView.as_view(), name='toggle-organization-status'),
    path('invite-college-admin/', InviteCollegeAdminView.as_view(), name='invite-college-admin'),
    path('setup-account/', SetupAccountView.as_view(), name='setup-account'),
]
