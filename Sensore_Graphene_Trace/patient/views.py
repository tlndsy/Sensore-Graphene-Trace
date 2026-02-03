from django.shortcuts import render, HttpResponse

# Create your views here.
def stats(request):
    return HttpResponse("This is the patients stats page (e.g., graph, heatmap")