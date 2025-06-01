from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from tasks.models import Administrador, Gerente, Buque
from django.contrib import messages
from django.urls import reverse
from .decorator import role_required
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt 
from django.views.decorators.http import require_http_methods
import json


# Create your views here.

def home(request):
    return render(request, 'home.html')

def login(request):
    return render(request, 'login.html')

def autentificacion_usuario(request):
    if request.method == 'POST':
        carnet_inresado = request.POST.get('username')
        password_ingresada = request.POST.get('password')

        if not carnet_inresado or not password_ingresada:
            return JsonResponse({'error': 'Faltan credenciales'}, status=400)

        user_role = None 
        user_obj = None 

        try:
            user_obj = Administrador.objects.get(
                carnet_admin=carnet_inresado,
                password_admin=password_ingresada
            )
            user_role = 'admin'
        except Administrador.DoesNotExist:
            pass 

        if user_role is None: 
            try:
                user_obj = Gerente.objects.get(
                    carnet_gerente=carnet_inresado, 
                    password_gerente=password_ingresada
                )
                user_role = 'gerente'
            except Gerente.DoesNotExist:
                return JsonResponse({'error': 'Credenciales inválidas'}, status=401)

        if user_role:
            request.session['user_id'] = user_obj.pk 
            request.session['username'] = carnet_inresado
            request.session['user_role'] = user_role 

            # Redirigir según el rol
            if user_role == 'admin':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('admin_view')}, status=200)
            elif user_role == 'gerente':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('gerente_view')}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    # Proteger esta vista para que solo sea accesible por administradores
    if request.session.get('user_role') != 'admin':
        messages.error(request, 'Acceso denegado. No eres administrador.')
        return redirect('no-permisos/') # Asumo que tienes una URL 'login_page'

    # Renderizar el dashboard completo
    return render(request, 'gerente.html', {
        'username': request.session.get('username'),
        'role': request.session.get('user_role')
    })

@role_required(allowed_roles=['gerente'])
def gerente_dashboard(request):
    # Proteger esta vista para que solo sea accesible por gerentes
    if request.session.get('user_role') != 'gerente':
        messages.error(request, 'Acceso denegado. No eres gerente.')
        return redirect('no-permisos/')

    # Renderizar el dashboard limitado
    return render(request, 'incompleto.html', {
        'username': request.session.get('username'),
        'role': request.session.get('user_role')
    })
    

def sin_permisos(request):
    return render(request, 'sinpermiso.html', {
        'message': 'No tienes los permisos necesarios para acceder a esta sección.',
        'username': request.session.get('username', 'Invitado')
    })

def logout_view(request):
    request.session.flush()
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect(reverse('login'))


@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "POST"])
def gerente_list_create(request):
    if request.method == 'GET':
        gerentes_data = []
        for gerente in Gerente.objects.all():
            gerentes_data.append({
                'carnet_gerente': gerente.carnet_gerente,
                'nombre': gerente.nombre_gerente,
                'contrasenia': gerente.password_gerente,
                'email': gerente.email,
            })
        return JsonResponse(gerentes_data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            carnet = data.get('carnet_gerente')
            nombre = data.get('nombre')
            password = data.get('password')
            email = data.get('email')

            if not all([carnet, nombre, password, email]):
                return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)

            if Gerente.objects.filter(carnet_gerente=carnet).exists():
                return JsonResponse({'error': 'El carnet de gerente ya existe'}, status=409)

            # hashed_password = make_password(password) # Descomentar para hashing
            nuevo_gerente = Gerente.objects.create(
                carnet_gerente=carnet,
                nombre_gerente=nombre,
                password_gerente=password,
                # password_gerente=hashed_password, # Descomentar para hashing
                email=email,
            )
            return JsonResponse({'message': 'Gerente creado exitosamente', 'carnet_gerente': nuevo_gerente.carnet_gerente}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@role_required(allowed_roles=['admin'])
@require_http_methods(["PUT", "DELETE"])
def gerente_retrieve_update_delete(request, carnet_gerente):
    gerente = get_object_or_404(Gerente, carnet_gerente=carnet_gerente)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nuevo_carnet = data.get('carnet_gerente') # Recibir el carnet (puede ser nuevo o el mismo)
            nombre = data.get('nombre')
            password = data.get('password')
            email = data.get('email')

            if not all([nuevo_carnet, nombre, email]):
                return JsonResponse({'error': 'Faltan campos obligatorios para actualizar'}, status=400)

            gerente.nombre_gerente = nombre
            if password:
                # gerente.password_gerente = make_password(password)
                gerente.password_gerente = password
            gerente.email = email
            gerente.save()

            return JsonResponse({'message': 'Gerente actualizado exitosamente', 'carnet_gerente': gerente.carnet_gerente}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            gerente.delete()
            return JsonResponse({'message': 'Gerente eliminado exitosamente'}, status=204)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@role_required(allowed_roles=['admin'])    
def ver_navios(request):
    return render(request, 'navio.html')


@require_http_methods(["GET"])
def gerente_list(request):
    gerentes_data = []
    for gerente in Gerente.objects.all().order_by('nombre_gerente'):
        gerentes_data.append({
            'carnet_gerente': gerente.carnet_gerente,
            'nombre_gerente': gerente.nombre_gerente,
        })
    return JsonResponse(gerentes_data, safe=False)


###########

def gerente_list(request):
    print("DEBUG: Entrando a gerente_list. Método:", request.method) # Para depuración
    try:
        gerentes_data = []
        for gerente in Gerente.objects.all().order_by('nombre_gerente'):
            gerentes_data.append({
                # Cambiado de 'id_gerente' a 'carnet_gerente'
                'carnet_gerente': gerente.carnet_gerente, 
                'nombre_gerente': gerente.nombre_gerente,
            })
        print(f"DEBUG: Retornando {len(gerentes_data)} gerentes desde gerente_list.") # Para depuración
        return JsonResponse(gerentes_data, safe=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: Excepción en gerente_list: {e}")
        return JsonResponse({'error': f'Error interno del servidor en gerente_list: {str(e)}'}, status=500)


@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "POST"])
def buque_list_create(request):
    if request.method == 'GET':
        buques_data = []
        for buque in Buque.objects.all().order_by('nombre_buque'):
            buques_data.append({
                # Cambiado de 'id_buque' a 'matricula_buque'
                'matricula_buque': buque.matricula_buque, 
                'nombre_buque': buque.nombre_buque,
                # 'matricula' ya no es un atributo separado, es la PK 'matricula_buque'
                'servicio': buque.servicio, 
                # Cambiado de 'gerente' a 'carnet_gerente'
                'carnet_gerente': buque.carnet_gerente.carnet_gerente if buque.carnet_gerente else None, 
                'administrador': None, # Siempre None en la respuesta GET para este campo
            })
        return JsonResponse(buques_data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_buque = data.get('nombre_buque')
            # Cambiado de 'matricula' a 'matricula_buque'
            matricula_buque = data.get('matricula_buque') 
            servicio = data.get('servicio') 
            # Cambiado de 'gerente' a 'carnet_gerente'
            carnet_gerente = data.get('carnet_gerente') 
            
            if not nombre_buque or not matricula_buque:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios.'}, status=400)
            
            servicio = servicio if servicio else None 
            carnet_gerente = carnet_gerente if carnet_gerente else None 

            gerente_instance = None
            if carnet_gerente is not None: 
                try:
                    # Buscar gerente por carnet_gerente
                    gerente_instance = Gerente.objects.get(carnet_gerente=carnet_gerente) 
                except Gerente.DoesNotExist: # No es necesario ValueError, ya que carnet_gerente es CharField
                    return JsonResponse({'error': f'El gerente seleccionado con Carnet "{carnet_gerente}" no es válido o no existe.'}, status=400)
            
            # Verificar si la matrícula ya existe
            if Buque.objects.filter(matricula_buque=matricula_buque).exists():
                return JsonResponse({'error': f'La matrícula "{matricula_buque}" ya existe en otro navío. Por favor, ingrese una matrícula única.'}, status=409)

            # Ya no necesitas max_id o new_id si matricula_buque es la PK
            nuevo_buque = Buque.objects.create(
                matricula_buque=matricula_buque, # Usar matricula_buque como PK
                nombre_buque=nombre_buque,
                servicio=servicio,
                carnet_gerente=gerente_instance, # Usar 'carnet_gerente' que es el nombre del campo ForeignKey
                carnet_admin=None, # Asumo que id_administrador se mapea a carnet_admin
            )
            return JsonResponse({
                'message': 'Navío creado exitosamente',
                'matricula_buque': nuevo_buque.matricula_buque, # Retornar matricula_buque
                'nombre_buque': nuevo_buque.nombre_buque,
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido. Verifique el formato.'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc() 
            print(f"ERROR: Error inesperado al crear buque: {e}") 
            return JsonResponse({'error': f'Error interno del servidor al crear navío: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método HTTP no permitido para esta operación.'}, status=405)


@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "PUT", "DELETE"])
# Cambiado de 'id_buque' a 'matricula_buque' en la URL
def buque_retrieve_update_delete(request, matricula_buque): 
    # Buscar buque por matricula_buque
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)

    if request.method == 'GET':
        return JsonResponse({
            'matricula_buque': buque.matricula_buque, # Retornar matricula_buque
            'nombre_buque': buque.nombre_buque,
            'servicio': buque.servicio,
            # Cambiado de 'gerente' a 'carnet_gerente'
            'carnet_gerente': buque.carnet_gerente.carnet_gerente if buque.carnet_gerente else None,
            'administrador': None, # Siempre None en la respuesta GET según tu lógica
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nombre_buque = data.get('nombre_buque')
            # La matrícula_buque ahora es la PK, no se actualiza (o si se actualiza, es un cambio de PK)
            # Generalmente, las PKs no se actualizan directamente, sino que se crea una nueva.
            # Aquí asumimos que la matrícula_buque del parámetro de URL es la matrícula a actualizar.
            # Y el body de la petición no debería contenerla para PUT si es la PK.
            # Sin embargo, si el frontend envía 'matricula_buque' en el body, la validamos.
            nueva_matricula_buque = data.get('matricula_buque') # Si se envía en el body para validar

            servicio = data.get('servicio')
            carnet_gerente = data.get('carnet_gerente')

            if not nombre_buque: # matricula_buque no es obligatoria en el body para PUT si es la PK del URL
                return JsonResponse({'error': 'El nombre del navío es obligatorio para actualizar.'}, status=400)
            
            # Si se intenta cambiar la matrícula_buque (PK)
            if nueva_matricula_buque and nueva_matricula_buque != matricula_buque:
                 return JsonResponse({'error': 'No se permite cambiar la matrícula de un navío existente. Elimine y cree uno nuevo si necesita cambiar la matrícula.'}, status=400)


            servicio = servicio if servicio else None
            carnet_gerente = carnet_gerente if carnet_gerente else None

            gerente_instance = None
            if carnet_gerente is not None:
                try:
                    gerente_instance = Gerente.objects.get(carnet_gerente=carnet_gerente)
                except Gerente.DoesNotExist:
                    return JsonResponse({'error': f'El gerente seleccionado con Carnet "{carnet_gerente}" no es válido o no existe.'}, status=400)

            buque.nombre_buque = nombre_buque
            buque.servicio = servicio
            buque.carnet_gerente = gerente_instance # Usar carnet_gerente
            buque.carnet_admin = None # Asumo que id_administrador se mapea a carnet_admin
            buque.save()

            return JsonResponse({'message': 'Navío actualizado exitosamente'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido.'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR: Error inesperado al actualizar buque: {e}")
            return JsonResponse({'error': f'Error interno del servidor al actualizar navío: {str(e)}'}, status=500)

    elif request.method == 'DELETE':
        try:
            buque.delete()
            return JsonResponse({'message': 'Navío eliminado exitosamente'}, status=204)
        except Exception as e:
            print(f"ERROR: Error inesperado al eliminar buque: {e}")
            return JsonResponse({'error': f'Error interno del servidor al eliminar navío: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método HTTP no permitido para esta operación.'}, status=405)

