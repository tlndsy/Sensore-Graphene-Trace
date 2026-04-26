import random

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect
from django.views.generic import TemplateView

from .forms import RegisterForm, LoginForm, CompleteProfileForm
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password

from .mixins import GroupRequiredMixin
from .models import PasswordResetCode
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from user.models import Message, Conversation, User, PatientClinician, PressureMapReading
import json
from Sensore_Graphene_Trace import global_constants as constants
from .utils import notifications


# Method to login the user
def login_user(request):
    login_form = LoginForm(request, data=request.POST)
    if login_form.is_valid():
        login(request, login_form.get_user())
        user = request.user
        # Redirect users who haven't completed their profile (e.g., new google users)
        if redirect_response := redirect_if_profile_incomplete(request):
            return redirect_response
        return redirect_to_home(request)
    return None


# Registers the user and redirects them to the home page
def register_user(request):
    register_form = RegisterForm(request.POST)
    if register_form.is_valid(): register_form.save(); print("Registration success"); return redirect("home")
    print("Registration failed")
    return None


# Sends the user a verification code for their password reset
def request_password_reset(request):
    from random import SystemRandom
    cryptogen = SystemRandom()
    # Get the users email
    email = request.POST.get("email")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:  # User doesn't exist
        return render(request, "user_home.html",
                      {"error": "No account with that email."})
    code = str(random.randint(100000, 999999))  # Generate a random 6 digit code
    # code = str(cryptogen.randrange(100000, 100000))
    PasswordResetCode.objects.create(user=user,
                                     code=code)  # Add to db
    send_mail("Your password reset code",  # Subject
              f"Your reset code is: {code}",  # Message
              "sensoregraphenetrace@gmail.com",  # From email
              [email], fail_silently=False)  # Recipient list
    return render(request, "user_home.html", {"reset_step": 2, "reset_email": email,
                                              "error": "No account with that email."})


# Method for the user to reset their password
def confirm_password_reset(request):
    email = request.POST.get("email")
    code = request.POST.get("code")
    password = request.POST.get("password")
    try:
        user = User.objects.get(email=email)
        reset = PasswordResetCode.objects.filter(user=user, code=code).latest("created_at")
        if not reset.is_valid():
            raise Exception("Expired")  # Checks if their code has expired
        user.password = make_password(password)
        user.save()
        reset.delete()
        return redirect("home")
    except Exception:
        return render(request, "user_home.html",
                      {"error": "Invalid or expired code."})


# Redirects the user to their correct home page based on their role upon logging in
def redirect_to_home(request):
    if request.user.is_authenticated:
        if redirect_response := redirect_if_profile_incomplete(request):
            return redirect_response  # Incomplete profile
        user_groups = request.user.groups.values_list("name", flat=True)
        if constants.ADMIN in user_groups: return redirect("user:administrator:home")  # Admin home page
        if constants.CLINICIAN in user_groups: return redirect("user:clinician:profile")  # Clinician profile
        if constants.PATIENT in user_groups: return redirect("user:patient:home")  # Patient home page
        return redirect("home")  # No group assigned to user
    return redirect("home")  # User is not authenticated


# Redirects users who have registered with Google to complete their profile
def redirect_if_profile_incomplete(request):
    if not request.user.date_of_birth or not request.user.phone_number:
        return redirect("user:complete_profile")
    return None


# Patient home pahe
def home(request):
    if request.user.is_authenticated:
        # Checks if user needs to complete their profile
        if redirect_response := redirect_if_profile_incomplete(request): return redirect_response
    # Specifies forms
    login_form = LoginForm()
    register_form = RegisterForm()
    reset_password_form = PasswordResetForm()
    # Checks which form is posting
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


# Registers user
def register(request):
    return render(request, "register.html", {})


# Logs out the user
def logout_user(request):
    logout(request)
    request.session.flush()  # Flushes user session
    return redirect('user:home')


# Complete profile page
@login_required
def complete_profile(request):
    user = request.user
    if request.method == "POST":
        form = CompleteProfileForm(request.POST, instance=user)
        if form.is_valid(): # Only change page if the form is valid
            form.save()
            return redirect("user:patient:home")
    else:
        form = CompleteProfileForm(instance=user)
    return render(request, "complete_profile.html", {"form": form})


class UserNotifications(GroupRequiredMixin, TemplateView):
    template_name = "user/user_notifications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["num_notifications"] = notifications.get_notification_count(self.request.user)
        context["notifications"] = notifications.get_notifications(self.request.user)

        return context


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
        # Report attachment
        'report': {
            'id': m.pressure_map_reading.id,
            'timestamp': m.pressure_map_reading.timestamp.strftime('%Y-%m-%d %H:%M'),
            'metrics_url': m.pressure_map_reading.metrics.url if m.pressure_map_reading.metrics else None,
        } if m.pressure_map_reading else None,
        # File attachment
        'attachment': m.attachment.url if m.attachment else None,
    } for m in messages]

    return JsonResponse({'messages': data})


@login_required
def get_assigned_clinicians(request):
    # ← fixed: patient/clinician not Patient_ID/Clinician_ID
    assigned = PatientClinician.objects.filter(
        patient=request.user
    ).select_related('clinician')

    return JsonResponse({
        'clinicians': [
            {
                'id': str(pc.clinician.id),
                'name': f"{pc.clinician.first_name} {pc.clinician.last_name}",
                'email': pc.clinician.email,
                'unread': Message.objects.filter(
                    sender=pc.clinician,
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
            other_user = User.objects.get(id=patient_id)
        else:
            clinician_id = request.GET.get('clinician_id')
            if clinician_id:
                other_user = User.objects.get(id=clinician_id)
            else:
                # fallback to first assigned clinician
                patient_clinician = PatientClinician.objects.filter(
                    patient=request.user  # ← fixed
                ).select_related('clinician').first()

                if not patient_clinician:
                    return JsonResponse({'error': 'No clinician assigned'})

                other_user = patient_clinician.clinician  # ← fixed

        # Find existing conversation between these two users
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()

        if not conversation:
            conversation = Conversation.objects.create(
                subject=f"Chat between {request.user.first_name} and {other_user.first_name}"
            )
            # ← add both users as participants
            conversation.participants.add(request.user, other_user)

        return JsonResponse({
            'conversation_id': conversation.id,
            'clinician_name': f"{other_user.first_name} {other_user.last_name}",
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def send_message(request):
    try:
        # Handle both JSON and FormData (for file uploads)
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
            conversation_id = data.get('conversation_id')
            content = data.get('content', '')
            report_id = data.get('report_id')  # ← for sending reports
            attachment = None
        else:
            conversation_id = request.POST.get('conversation_id')
            content = request.POST.get('content', '')
            report_id = request.POST.get('report_id')
            attachment = request.FILES.get('attachment')

        conversation = get_object_or_404(Conversation, id=conversation_id)

        # Find recipient — the other participant
        recipient = conversation.participants.exclude(id=request.user.id).first()

        if not recipient:
            return JsonResponse({'error': 'No recipient found'}, status=404)

        # Link report if provided
        pressure_map_reading = None
        if report_id:
            try:
                pressure_map_reading = PressureMapReading.objects.get(id=report_id)
            except PressureMapReading.DoesNotExist:
                pass

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            recipient=recipient,
            content=content,
            attachment=attachment,
            pressure_map_reading=pressure_map_reading,  # ← attach report
        )

        return JsonResponse({
            'status': 'ok',
            'message_id': message.id,
            'timestamp': message.timestamp.strftime('%H:%M'),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def unread_count(request):
    count = Message.objects.filter(
        recipient=request.user,
        read_receipt=False
    ).count()
    return JsonResponse({'count': count})


@login_required
def clinician_conversations(request):
    assigned_patients = PatientClinician.objects.filter(
        clinician=request.user
    ).select_related('patient')

    return JsonResponse({
        'patients': [
            {
                'name': f"{p.patient.first_name} {p.patient.last_name}",
                'user_id': str(p.patient.id),
                'unread': Message.objects.filter(
                    recipient=request.user,
                    sender=p.patient,
                    read_receipt=False
                ).count()
            }
            for p in assigned_patients
        ]
    })


@login_required
def get_patient_reports(request):
    readings = PressureMapReading.objects.filter(
        reading_equipment__user=request.user
    ).order_by('-timestamp')[:10]

    return JsonResponse({
        'reports': [
            {
                'id': r.id,
                'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M'),
                'has_metrics': bool(r.metrics),  # ← just show if metrics exist
                'metrics_url': r.metrics.url if r.metrics else None,
            }
            for r in readings
        ]
    })
