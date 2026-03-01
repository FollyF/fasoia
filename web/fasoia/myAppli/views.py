from django.shortcuts import render
from .models import *


def home(request):
    return render(request, 'myAppli/home.html')

def opportunites(request):
    offre_uemoa = Offre_uemoa.objects.all()
    ami = Ami_uemoa.objects.all()
    context = {
        'offre': offre_uemoa,
        'ami' : ami    
    }
    return render(request, 'myAppli/opportunites.html', context)

def connexion(request):
    return render(request, 'myAppli/connexion.html')
   
def inscription(request):
    return render(request, 'myAppli/inscription.html')   