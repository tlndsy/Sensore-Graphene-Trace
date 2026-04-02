from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect
from .forms import RegisterForm, LoginForm


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from user.models import Message, Conversation, User, PatientClinician
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

