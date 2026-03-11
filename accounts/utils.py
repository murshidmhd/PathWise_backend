import random
from django.core.mail import send_mail
from .models import OTP


def generate_otp():
    return str(random.randint(100000, 999999))  # 6 digit OTP


def send_otp_email(email):
    otp = generate_otp()
    print(otp)

    # Delete any old OTPs for this email
    OTP.objects.filter(email=email).delete()

    # Save new OTP
    OTP.objects.create(email=email, otp=otp)

    # Send email
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP code is: {otp}. It expires in 5 minutes.",
        from_email="your_email@gmail.com",
        recipient_list=[email],
    )
