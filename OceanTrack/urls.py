from django.contrib import admin
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('api/login/', views.autentificacion_usuario, name='api_login'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_view'),
    path('dashboard/gerente/', views.gerente_dashboard, name='gerente_view'),
    path('Denegado/', views.sin_permisos, name='no_permission'),
    path('logout/', views.logout_view, name='logout'),
    path('api/gerentes/list/', views.gerente_list, name='api_gerente_list'),
    path('api/gerentes/', views.gerente_list_create, name='api_gerente_list_create'),
    path('api/gerentes/<str:carnet_gerente>/', views.gerente_retrieve_update_delete, name='api_gerente_retrieve_update_delete'), # Para editar/eliminar
    path('buques/', views.ver_navios, name='buques'),
    path('api/navios/', views.buque_list_create, name='buque_list_create'),
    path('api/navios/<str:matricula_buque>/', views.buque_retrieve_update_delete, name='navio_detail'),
    # path('navios/inventario/<str:matricula_buque>/', views.inventario_view, name='inventario_buque'),

    


]
