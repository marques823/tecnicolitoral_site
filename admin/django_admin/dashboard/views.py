from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def index(request):
    """Página inicial do painel administrativo"""
    # Se o usuário estiver autenticado, mostra a página inicial personalizada
    if request.user.is_authenticated:
        return render(request, 'dashboard/index.html', {
            'title': 'Painel Administrativo - Técnico Litoral',
        })
    # Se não estiver autenticado, redireciona para a página de login
    return redirect('admin:index')

@login_required
def dashboard(request):
    """Página principal do dashboard"""
    return render(request, 'dashboard/dashboard.html', {
        'title': 'Dashboard - Técnico Litoral',
    })
