from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, HttpResponse, redirect


# Create your views here.
def home(request):

    login_form = AuthenticationForm(request)
    register_form = UserCreationForm()
    if request.method == 'POST':

        if request.POST.get("form_type") == "login":
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                print("Login success") # Will adapt when the home page exists

        if request.POST.get("form_type") == "register":
            register_form = UserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                print("Registration success")
                return redirect('home')

    return render(request, "home.html", {"form":login_form, "register_form":register_form})

def register(request):
    return render(request, "register.html", {})


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from user.models import Message, Conversation, User, PatientClinician
import json


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
def get_or_create_conversation(request):
    # Find the clinician linked to this patient
    patient_clinician = PatientClinician.objects.filter(
        Patient_ID=request.user
    ).first()

    if not patient_clinician:
        return JsonResponse({'error': 'No clinician assigned'}, status=404)

    clinician = patient_clinician.Clinician_ID

    # Find existing conversation or create one
    existing = Message.objects.filter(
        sender=request.user, recipient=clinician
    ).values_list('conversation', flat=True).first()

    if existing:
        conversation = Conversation.objects.get(id=existing)
    else:
        conversation = Conversation.objects.create(
            subject=f"Chat: {request.user.first_name} & {clinician.first_name}"
        )

    return JsonResponse({
        'conversation_id': conversation.id,
        'clinician_name': clinician.first_name + ' ' + clinician.last_name,
    })


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
