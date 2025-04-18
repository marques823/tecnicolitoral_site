from django.shortcuts import render

# Create your views here.

def home(request):
    """Página inicial do site"""
    return render(request, 'website/home.html', {
        'title': 'Técnico Litoral - Serviços de Informática e Tecnologia',
    })

def about(request):
    """Página Sobre Nós"""
    return render(request, 'website/about.html', {
        'title': 'Sobre Nós - Técnico Litoral',
    })

def services(request):
    """Página de Serviços"""
    return render(request, 'website/services.html', {
        'title': 'Nossos Serviços - Técnico Litoral',
    })

def contact(request):
    """Página de Contato"""
    return render(request, 'website/contact.html', {
        'title': 'Contato - Técnico Litoral',
    })
