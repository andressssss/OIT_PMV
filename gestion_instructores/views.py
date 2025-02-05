from django.shortcuts import render

# Create your views here.
def gestion_instructor(request):
    return render(request, 'gestion_instructor.html')