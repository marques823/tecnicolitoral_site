"""
URL configuration for tecnicolitoral_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Site principal na raiz
    path('', include('website.urls')),
    
    # Painel administrativo Django
    path('admin/django/', admin.site.urls),
    
    # Painel personalizado em /admin
    path('admin/', include('dashboard.urls', namespace='dashboard_admin')),
    
    # Redirecionamento ao sair do admin do Django
    path('admin/django/logout/', RedirectView.as_view(pattern_name='dashboard_admin:index'), name='admin-logout'),
]

# Personaliza os títulos do admin
admin.site.site_header = 'Administração Técnico Litoral'
admin.site.site_title = 'Painel Administrativo'
admin.site.index_title = 'Bem-vindo ao Painel de Gestão'
