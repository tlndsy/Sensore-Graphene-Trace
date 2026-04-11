from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect
from .forms import RegisterForm, LoginForm


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from user.models import Message, Conversation, User, PatientClinician, PressureMapReading
import json


# Create your views here.
def home(request):
    login_form = LoginForm()
    register_form = RegisterForm()
    if request.method == 'POST':
        if request.POST.get("form_type") == "login":
            login_form =LoginForm(request, data=request.POST)
            if login_form.is_valid():
                print("Login success")
                login(request, login_form.get_user())
                return redirect('user:patient:home')

        elif request.POST.get("form_type") == "register":
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                print("Registration success")
                return redirect('home')
            else:
                print("Registration failed")

    return render(request, "home.html", {"form":login_form, "register_form":register_form})

def register(request):
    return render(request, "register.html", {})

def logout_view(request):
    logout(request)
    return redirect('home')



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
