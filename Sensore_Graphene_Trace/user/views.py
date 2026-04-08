from django.contrib.auth.forms import AuthenticationForm, UserCreationForm,PasswordResetForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect
from .forms import RegisterForm, LoginForm, CompleteProfileForm
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from .models import PasswordResetCode
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from user.models import Message, Conversation, User, PatientClinician
import json
from Sensore_Graphene_Trace import global_constants as constants

# Create your views here.
def login_user(request):
    login_form = LoginForm(request, data=request.POST)
    if login_form.is_valid():
        login(request, login_form.get_user()); user = request.user
        if redirect_response := redirect_if_profile_incomplete(request): return redirect_response
        if request.session.pop('needs_profile_completion', False): return redirect("complete_profile")
        return redirect("user:patient:home")
    return None

# Registers the user and redirects them to the home page
def register_user(request):
    register_form = RegisterForm(request.POST)
    if register_form.is_valid(): register_form.save(); print("Registration success"); return redirect("home")
    print("Registration failed")
    return None

# Sends the user a verification code for their password reset
def request_password_reset(request):
    email = request.POST.get("email")
    try: user = User.objects.get(email=email)
    except User.DoesNotExist: return render(request, "user_home.html", {"error": "No account with that email."})
    code = str(random.randint(100000, 999999))
    PasswordResetCode.objects.create(user=user, code=code)
    send_mail("Your password reset code",f"Your reset code is: {code}","sensoregraphenetrace@gmail.com",
        [email],fail_silently=False)
    return render(request, "user_home.html", {"reset_step": 2,"reset_email": email})

# Method for the user to reset their password
def confirm_password_reset(request):
    email = request.POST.get("email"); code = request.POST.get("code"); password = request.POST.get("password")
    try:
        user = User.objects.get(email=email)
        reset = PasswordResetCode.objects.filter(user=user, code=code).latest("created_at")
        if not reset.is_valid(): raise Exception("Expired") # Checks if their code has expired
        user.password = make_password(password); user.save(); reset.delete()
        return redirect("home")
    except Exception:
        return render(request, "user_home.html", {"error": "Invalid or expired code."})

# Redirects the user to their correct home page based on their role upon logging in
def redirect_to_home(request):
    if request.user.is_authenticated:
        if redirect_response := redirect_if_profile_incomplete(request): return redirect_response # Incomplete profile
        user_groups = request.user.groups.values_list("name", flat=True)
        if constants.ADMIN in user_groups: return redirect("user:administrator:home") # Admin home page
        if constants.CLINICIAN in user_groups: return redirect("user:clinician:home") # Clinician home page
        if constants.PATIENT in user_groups: return redirect("user:patient:home") # Patient home page
        return redirect("home") # No group assigned to user
    return redirect("home") # User is not authenticated

# Redirects users who have registered with Google to complete their profile
def redirect_if_profile_incomplete(request):
    if not request.user.date_of_birth or not request.user.phone_number: return redirect("user:complete_profile")
    return None
def home(request):
    if request.user.is_authenticated:
        if redirect_response := redirect_if_profile_incomplete(request): return redirect_response
    login_form = LoginForm(); register_form = RegisterForm(); reset_password_form = PasswordResetForm()
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "login":
            response = login_user(request)
        elif form_type == "register":
            response = register_user(request)
        elif form_type == "request_reset_code":
            return request_password_reset(request)
        elif form_type == "confirm_reset":
            return confirm_password_reset(request)
        if response:
            return response

    return render(request, "user_home.html", {
        "form": login_form,
        "register_form": register_form,
        "reset_password_form": reset_password_form
    })

def register(request):
    return render(request, "register.html", {})

def logout_user(request):
    logout(request)
    request.session.flush()
    return redirect('home')

@login_required
def complete_profile(request):
    user = request.user
    if request.method == "POST":
        form = CompleteProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("user:patient:home")
    else: form = CompleteProfileForm(instance=user)
    return render(request, "complete_profile.html", {"form": form})

@login_required
def get_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')

    # Mark messages as read
    messages.filter(recipient=request.user).update(read_receipt=True)

    data = [{
        'id': m.id,
        'content': m.content,
        'sender': m.sender.first_name,
        'timestamp': m.timestamp.strftime('%H:%M'),
        'is_me': m.sender == request.user,
    } for m in messages]

    return JsonResponse({'messages': data})

@login_required
def get_assigned_clinicians(request):
    assigned = PatientClinician.objects.filter(
        Patient_ID=request.user
    ).select_related('Clinician_ID')

    return JsonResponse({
        'clinicians': [
            {
                'id': str(pc.Clinician_ID.id),
                'name': f"{pc.Clinician_ID.first_name} {pc.Clinician_ID.last_name}",
                'email': pc.Clinician_ID.email,
                'unread': Message.objects.filter(
                    sender=pc.Clinician_ID,
                    recipient=request.user,
                    read_receipt=False
                ).count()
            }
            for pc in assigned
        ]
    })


@login_required
def get_or_create_conversation(request):
    try:
        if request.user.role == 'CLINICIAN':
            patient_id = request.GET.get('patient_id')
            from user.models import User
            other_user = User.objects.get(id=patient_id)
        else:
            # Patient — clinician_id now passed from frontend
            clinician_id = request.GET.get('clinician_id')

            if clinician_id:
                from user.models import User
                other_user = User.objects.get(id=clinician_id)
            else:
                # fallback to first assigned clinician
                patient_clinician = PatientClinician.objects.filter(
                    Patient_ID=request.user
                ).select_related('Clinician_ID').first()

                if not patient_clinician:
                    return JsonResponse({'error': 'No clinician assigned'})

                other_user = patient_clinician.Clinician_ID

        conversation = Conversation.objects.filter(
            message__sender=request.user,
            message__recipient=other_user
        ).first() or Conversation.objects.filter(
            message__sender=other_user,
            message__recipient=request.user
        ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                subject=f"Chat between {request.user.first_name} and {other_user.first_name}"
            )

        return JsonResponse({
            'conversation_id': conversation.id,
            'clinician_name': f"{other_user.first_name} {other_user.last_name}",
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def send_message(request):
    data = json.loads(request.body)
    conversation_id = data.get('conversation_id')
    content = data.get('content')

    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Find recipient (the other person in the conversation)
    patient_clinician = PatientClinician.objects.filter(
        Patient_ID=request.user
    ).first()

    if not patient_clinician:
        return JsonResponse({'error': 'No clinician assigned'}, status=404)

    recipient = patient_clinician.Clinician_ID

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        recipient=recipient,
        content=content,
    )

    return JsonResponse({
        'status': 'ok',
        'message_id': message.id,
        'timestamp': message.timestamp.strftime('%H:%M'),
    })


@login_required
def unread_count(request):
    count = Message.objects.filter(
        recipient=request.user,
        read_receipt=False
    ).count()
    return JsonResponse({'count': count})

