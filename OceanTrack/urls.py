from django.contrib import admin
from django.urls import path
from tasks import views  # Asegúrate de que 'tasks' es el nombre de tu aplicación
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('api/login/', views.autentificacion_usuario, name='api_login'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_view'),
    path('dashboard/gerente/', views.gerente_dashboard, name='gerente_view'),
    path('Denegado/', views.sin_permisos, name='no_permission'),
    path('logout/', views.logout_view, name='logout'),
    
    path('api/administradores/', views.api_administrador_create, name='api_administrador_create'),

    # Rutas para Gerentes (que ya tenías)
    path('api/gerentes/list/', views.gerente_list, name='api_gerente_list'),
    path('api/gerentes/', views.gerente_list_create, name='api_gerente_list_create'),
    path('api/gerentes/<str:carnet_gerente>/', views.gerente_retrieve_update_delete, name='api_gerente_retrieve_update_delete'),

    # Rutas para Buques (que ya tenías)
    path('buques/', views.ver_navios, name='buques'),
    path('api/navios/', views.buque_list_create, name='buque_list_create'),
    path('api/navios/<str:matricula_buque>/', views.buque_retrieve_update_delete, name='navio_detail'),

    # ---- INICIO: Rutas para el CRUD de Productos (NUEVAS) ----
    path('inventario/<str:matricula_buque>/', views.catalogo_view, name='catalogos'),
    path('api/inventario/<str:matricula_buque>/productos/', views.api_productos_list_create, name='api_productos_list_create'),
    path('api/inventario/<str:matricula_buque>/productos/<str:id_producto>/', views.api_producto_detail_update_delete, name='api_producto_detail_update_delete'),
    # ---- FIN: Rutas para el CRUD de Productos ----
]

# Configuración para servir archivos de medios durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)