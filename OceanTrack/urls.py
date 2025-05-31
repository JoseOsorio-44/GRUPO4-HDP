"""
URL configuration for OceanTrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('api/login/', views.autentificacion_usuario, name='api_login'),
    path('dashboard/admin/', views.admin_dashboard, name='completo'),
    path('dashboard/gerente/', views.gerente_dashboard, name='incompleto'),
    path('Denegado/', views.sin_permisos, name='no_permission'),
    path('logout/', views.logout_view, name='logout'),
    path('api/gerentes/', views.gerente_list_create, name='api_gerente_list_create'),
    path('api/gerentes/<int:gerente_id>/', views.gerente_retrieve_update, name='api_gerente_retrieve_update'), # Para editar
    path('api/gerentes/<int:gerente_id>/', views.gerente_retrieve_update, name='api_gerente_delete'),
    path('buques/', views.ver_navios, name='buques'),
    path('api/navios/', views.buque_list_create, name='buque_list_create'),
    path('api/navios/<int:id_buque>/', views.buque_retrieve_update_delete, name='navio_detail'),
    path('api/gerentes/list/', views.gerente_list, name='api_gerente_list'),
    


]
