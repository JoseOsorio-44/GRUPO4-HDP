from django.urls import path
from . import views

app_name = 'inicio'

urlpatterns = [

    #Ruta por defecto
    path('', views.home, name='home'),
    
    #Ruta de inicio de sesion
    path('login/', views.login, name='login'),
    path('api/login/', views.autentificacion_usuario, name='api_login'),
    
    #Ruta a acceso denegado a vista
    path('Denegado/', views.sin_permisos, name='no_permission'),
    
    #Ruta a cierre desesion
    path('logout/', views.logout_view, name='logout'),
    
]
