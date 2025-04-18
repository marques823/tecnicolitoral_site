from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('sobre/', views.about, name='about'),
    path('servicos/', views.services, name='services'),
    path('contato/', views.contact, name='contact'),
] 