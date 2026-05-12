from .views import OrganizationListView, CreateCollegeAdminView, CreateOrganizationView
from django.urls import path
urlpatterns = [
    path('organizations/', OrganizationListView.as_view(), name='organization-list'),
    path('organizations/create/', CreateOrganizationView.as_view(), name='create-organization'),
    path('create-college-admin/', CreateCollegeAdminView.as_view(), name='create-college-admin'),
]
