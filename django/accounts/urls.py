from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    VerifyOTPView,
    ResendOTPView,
    GoogleAuthView,
    CompleteGoogleRegistrationView,
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view()),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("google/", GoogleAuthView.as_view()),
    path("complete-google-registration/", CompleteGoogleRegistrationView.as_view()),
    # path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    # path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
