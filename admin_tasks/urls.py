from django.urls import path
from . import views

app_name = 'admin_tasks'

urlpatterns = [

    #Ruta hacia vista de gerente
    path('dashboard/admin/', views.admin_dashboard, name='admin_view'),
    
    #Ruta para la creacion de un administrador
    path('api/administradores/', views.api_administrador_create, name='api_administrador_create'),

    # Rutas para Gerentes
    path('api/gerentes/list/', views.gerente_list, name='api_gerente_list'),
    path('api/gerentes/', views.gerente_list_create, name='api_gerente_list_create'),
    path('api/gerentes/<str:carnet_gerente>/', views.gerente_retrieve_update_delete, name='api_gerente_retrieve_update_delete'),

    # Rutas para Buques
    path('buques/', views.ver_navios, name='buques'),
    path('api/navios/', views.buque_list_create, name='buque_list_create'),
    path('api/navios/<str:matricula_buque>/', views.buque_retrieve_update_delete, name='navio_detail'),

    # Rutas para productos 
    path('inventario/<str:matricula_buque>/', views.catalogo_view, name='catalogos'),
    path('api/inventario/<str:matricula_buque>/productos/', views.api_productos_list_create, name='api_productos_list_create'),
    path('api/inventario/<str:matricula_buque>/productos/<str:codigo_producto_url>/', views.api_producto_detail_update_delete, name='api_producto_detail_update_delete'),
    
]
