# accounts/views.py

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import PhoneNumberForm, OTPForm, PasswordForm
from .models import User
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_otp(phone_number):
    phone_number = phone_number.strip()
    if not phone_number.startswith('+'):
        phone_number = f'+{phone_number}'
    
    try:
        verification = client.verify.v2.services(settings.TWILIO_VERIFY_SID) \
            .verifications \
            .create(to=phone_number, channel="sms")
        return verification.status
    except TwilioException as e:
        print(f"Error sending OTP: {e}")
        return None

def login_view(request):
    error_message = None
    phone_form = PhoneNumberForm(request.POST or None)
    password_form = PasswordForm(request.POST or None)
    
    if request.method == 'POST':
        if phone_form.is_valid():
            phone_number = phone_form.cleaned_data['phone_number']
            if phone_number == '+919876543210':
                if 'password' in request.POST:
                    if password_form.is_valid():
                        password = password_form.cleaned_data['password']
                        if password == '123456':
                            user, created = User.objects.get_or_create(phone_number=phone_number)
                            login(request, user)
                            return redirect('success')
                        else:
                            error_message = 'Invalid password'
                return render(request, 'accounts/login.html', {
                    'phone_form': phone_form,
                    'password_form': password_form,
                    'show_password': True,
                    'error_message': error_message,
                })
            else:
                status = send_otp(phone_number)
                if status == 'pending':
                    request.session['phone_number'] = phone_number
                    return redirect('verify_otp')
                else:
                    error_message = 'Failed to send OTP'
    return render(request, 'accounts/login.html', {
        'phone_form': phone_form,
        'password_form': password_form,
        'show_password': False,
        'error_message': error_message,
    })

def verify_otp_view(request):
    phone_number = request.session.get('phone_number')
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            try:
                verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SID) \
                    .verification_checks \
                    .create(to=phone_number, code=otp_code)
                if verification_check.status == 'approved':
                    user, created = User.objects.get_or_create(phone_number=phone_number)
                    login(request, user)
                    return redirect('success')
                else:
                    form.add_error('otp', 'Invalid OTP')
            except TwilioException as e:
                form.add_error('otp', f'Error verifying OTP: {e}')
    else:
        form = OTPForm()
    return render(request, 'accounts/verify_otp.html', {'form': form})

def success_view(request):
    return render(request, 'accounts/success.html')



