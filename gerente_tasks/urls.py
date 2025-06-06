from django.urls import path
from . import views

app_name = 'gerente_tasks'

urlpatterns = [

    #Ruta para vista de gerente.
    path('dashboard/gerente/', views.gerente_dashboard, name='gerente_view'),
    
    #Rutas para la consulta de productos.
    path('api/gerente/productos/', views.api_productos_gerente_list, name='api_productos_gerente_list'),
    path('api/gerente/productos/<str:codigo_producto>/', views.api_producto_gerente_detail, name='api_producto_gerente_detail'),
    path('api/gerente/productos/<str:codigo_producto>/update_cantidad/', views.api_producto_gerente_update_cantidad, name='api_producto_gerente_update_cantidad'),
    
]
