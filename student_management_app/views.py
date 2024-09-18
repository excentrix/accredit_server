from django.shortcuts import render,HttpResponse, redirect,HttpResponseRedirect
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.hashers import check_password
from .models import CustomUser, Staffs, Students, AdminHOD, NAAC,Parent
from django.contrib import messages


#OTP verification
from django.conf import settings
#from .forms import PhoneNumberForm, OTPForm, PasswordForm
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .forms import OTPForm



# client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_otp(phone_number):
    # This function is now a placeholder and does not actually send an OTP
    # You'll need to implement your own OTP sending logic here
    # For example, you could use email or a different OTP service
    print(f"Simulated sending OTP to {phone_number}")
    return "pending"  # Simulate a pending status
@csrf_exempt
def send_otp_view(request):
    phone_number = request.POST.get('phone_number')
    if not phone_number:
        return JsonResponse({'error': 'Phone number is required'}, status=400)

    status = send_otp(phone_number)
    if status:
        return JsonResponse({'status': status})
    return JsonResponse({'error': 'Failed to send OTP'}, status=500)
	
#@csrf_exempt
def verify_otp_view(request):
    phone_number = request.POST.get('phone_number')
    otp_code = request.POST.get('otp_code')

    if not phone_number or not otp_code:
        return JsonResponse({'error': 'Phone number and OTP code are required'}, status=400)

    # This is a placeholder for OTP verification logic
    # You'll need to implement your own verification method here
    if otp_code == "123456":  # Replace with your actual verification logic
            request.session['phone_number'] = phone_number
            return JsonResponse({'status': 'verified'})
    
    return JsonResponse({'error': 'Invalid OTP'}, status=400)

def home(request):
	return render(request, 'home.html')


def contact(request):
	return render(request, 'contact.html')


def loginUser(request):
	return render(request, 'login_page.html')

def doLogin(request):
    password = request.GET.get('password')
    mobile = request.GET.get('mobile')
    
    if not (mobile and password):
        messages.error(request, "Please provide all the details!")
        return render(request, 'login_page.html')

    # Find users with the given mobile number
    users_with_mobile = CustomUser.objects.filter(mobile=mobile)

    if not users_with_mobile.exists():
        messages.error(request, 'Invalid Login Credentials!')
        return render(request, 'login_page.html')

    # Iterate over the users to find the correct user based on password and user type
    user = None
    for u in users_with_mobile:
        if check_password(password, u.password):
            user = u
            break

    if user is None:
        messages.error(request, 'Invalid Login Credentials!')
        return render(request, 'login_page.html')

    # Log in the user
    login(request, user)

    # Redirect based on user type
    if user.user_type == CustomUser.STUDENT:
        return redirect('student_home/')
    elif user.user_type == CustomUser.STAFF:
        return redirect('staff_home/')
    elif user.user_type == CustomUser.HOD:
        return redirect('admin_home/')
    elif user.user_type == CustomUser.NAAC:
        return redirect('naac_home/')
    elif user.user_type == CustomUser.Parent:
        return redirect('parent_home/')

    return render(request, 'home.html')

"""
def doLogin(request):
    mobile = request.GET.get('mobile')
    password = request.GET.get('password')

    if not (mobile and password):
        messages.error(request, "Please provide all the details!")
        return render(request, 'login_page.html')

    try:
        user = CustomUser.objects.get(mobile=mobile)
    except CustomUser.DoesNotExist:
        messages.error(request, "Invalid Login Credentials!")
        return render(request, 'login_page.html')

    if check_password(password, user.password):
        login(request, user)

        if user.user_type == CustomUser.STUDENT:
            return redirect('student_home/')
        elif user.user_type == CustomUser.STAFF:
            return redirect('staff_home/')
        elif user.user_type == CustomUser.HOD:
            return redirect('admin_home/')
        elif user.user_type == CustomUser.NAAC:
            return redirect('naac_home/')
    else:
        messages.error(request, "Invalid Login Credentials!")
        return render(request, 'login_page.html')

    return render(request, 'home.html')


def doLogin(request):
	
	print("here")
	#email_id = request.GET.get('email')
	password = request.GET.get('password')
	mobile = request.GET.get('mobile')
	# user_type = request.GET.get('user_type')
	#print(email_id)
	print(password)
	print(mobile)
	print(request.user)
	if not (mobile and password):
		messages.error(request, "Please provide all the details!!")
		return render(request, 'login_page.html')

	user = CustomUser.objects.filter(mobile=mobile, password=password).last()
      
	if not user:
		messages.error(request, 'Invalid Login Credentials!!')
		return render(request, 'login_page.html')
    
	login(request, user)
	print(request.user)

	if user.user_type == CustomUser.STUDENT:
		return redirect('student_home/')
	elif user.user_type == CustomUser.STAFF:
		return redirect('staff_home/')
	elif user.user_type == CustomUser.HOD:
		return redirect('admin_home/')
	elif user.user_type == CustomUser.NAAC:	#
		return redirect('naac_home/')

	return render(request, 'home.html')
"""
	
def registration(request):
	return render(request, 'registration.html')
	
def get_user_type_mobile(request):
	
	if request.method == 'POST':
		mobile = request.POST.get('mobile')
		user = CustomUser.objects.filter(mobile = mobile).last()
		
		if user:
			user_type = user.user_type
	return user_type

def doRegistration(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile = request.POST.get('mobile')
        email_id = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        if not (email_id and password and confirm_password):
            messages.error(request, 'Please provide all the details!!')
            return render(request, 'registration.html')

        if password != confirm_password:
            messages.error(request, 'Both passwords should match!!')
            return render(request, 'registration.html')

        is_user_exists = CustomUser.objects.filter(email=email_id).exists()
        if is_user_exists:
            messages.error(request, 'User with this email id already exists. Please proceed to login!!')
            return render(request, 'registration.html')

        user_type = get_user_type_from_email(email_id)
        if user_type is None:
            messages.error(request, "Please use valid format for the email id: '<username>.<staff|student|hod|naac>@<college_domain>'")
            return render(request, 'registration.html')

        username = email_id.split('@')[0].split('.')[0]
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'User with this username already exists. Please use different username')
            return render(request, 'registration.html')

        user = CustomUser()
        user.username = username
        user.email = email_id
        user.password = password
        user.user_type = user_type
        user.first_name = first_name
        user.last_name = last_name
        user.mobile = mobile
        user.save()

        if user_type == CustomUser.STAFF:
            Staffs.objects.create(admin=user)
            return redirect('staff_home/')
        elif user_type == CustomUser.STUDENT:
            Students.objects.create(admin=user)
            return redirect('student_home/')
        elif user_type == CustomUser.HOD:
            AdminHOD.objects.create(admin=user)
            return redirect('admin_home/')
        elif user_type == CustomUser.NAAC:
            NAAC.objects.create(naac_admin=user)
            return redirect('naac_home/')
        elif user_type == CustomUser.Parent:
            Parent.objects.create(parent_admin=user)
            return redirect('parent_home/')
    
    
    return render(request, 'registration.html')

	
def logout_user(request):
	logout(request)
	return HttpResponseRedirect('/')


def get_user_type_from_email(email_id):
	"""
	Returns CustomUser.user_type corresponding to the given email address
	email_id should be in following format:
	'<username>.<staff|student|hod|naac>@<college_domain>'
	eg.: 'abhishek.staff@jecrc.com'
	"""

	try:
		email_id = email_id.split('@')[0]
		email_user_type = email_id.split('.')[1]
		return CustomUser.EMAIL_TO_USER_TYPE_MAP[email_user_type]
	except:
		return None
