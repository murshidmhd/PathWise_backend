from django.urls import path
from .views import RegisterView, LoginView, RefreshTokenView, MeView, LogoutView , VerifyOTPView , GoogleAuthView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view()),
    path("me/", MeView.as_view()),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path('google/', GoogleAuthView.as_view()), 


]
 