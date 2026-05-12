import random
from django.core.mail import send_mail
from django.core.cache import cache


def generate_otp():
    return str(random.randint(100000, 999999))


def create_otp(email):
    otp = generate_otp()
    # Store OTP in cache for 5 minutes
    print(otp)
    cache.set(f"otp:{email}", otp, timeout=300)
    return otp


def send_otp_email(email, otp):
    # Send email
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP code is: {otp}. It expires in 5 minutes.",
        from_email="your_email@gmail.com",
        recipient_list=[email],
    )
