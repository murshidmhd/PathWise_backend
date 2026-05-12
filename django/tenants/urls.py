from django.urls import path
from .views import OrganizationListView, CreateCollegeAdminView

urlpatterns = [
    path('organizations/', OrganizationListView.as_view(), name='organization-list'),
    path('create-college-admin/', CreateCollegeAdminView.as_view(), name='create-college-admin'),
]
