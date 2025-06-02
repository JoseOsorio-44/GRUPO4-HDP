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


#######filtrado de usuario################
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

            if user_role == 'gerente' and hasattr(user_obj, 'matricula_buque') and user_obj.matricula_buque:
                request.session['buque_matricula'] = user_obj.matricula_buque.matricula_buque
            else:
                request.session['buque_matricula'] = None

            if user_role == 'admin':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('admin_view')}, status=200)
            elif user_role == 'gerente':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('gerente_view')}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    # Ejemplo de acceso a datos de sesión
    carnet_admin_logueado = request.session.get('username')
    rol_logueado = request.session.get('user_role')
    # ... puedes usar carnet_admin_logueado para cualquier lógica específica ...
    return render(request, 'gerente.html', {
        'username': carnet_admin_logueado,
        'role': rol_logueado
    })

@role_required(allowed_roles=['gerente'])
def gerente_dashboard(request):
    # Ejemplo de acceso a datos de sesión
    carnet_gerente_logueado = request.session.get('username')
    rol_logueado = request.session.get('user_role')
    matricula_buque_asociada = request.session.get('buque_matricula')
    # ... puedes usar estos datos para cualquier lógica específica ...
    return render(request, 'incompleto.html', {
        'username': carnet_gerente_logueado,
        'role': rol_logueado,
        'buque_matricula': matricula_buque_asociada
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
    if request.session.get('user_role') != 'gerente':
        messages.error(request, 'Acceso denegado. No eres gerente.')
        return redirect('no-permisos/')

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

#########Control de gerentes#########

#creacion de lista de gerentes
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

            nuevo_gerente = Gerente.objects.create(
                carnet_gerente=carnet,
                nombre_gerente=nombre,
                password_gerente=password,
                email=email,
            )
            return JsonResponse({'message': 'Gerente creado exitosamente', 'carnet_gerente': nuevo_gerente.carnet_gerente}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

#actualizacion y creacion de gerente
@role_required(allowed_roles=['admin'])
@require_http_methods(["PUT", "DELETE"])
def gerente_retrieve_update_delete(request, carnet_gerente):
    gerente = get_object_or_404(Gerente, carnet_gerente=carnet_gerente)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nuevo_carnet = data.get('carnet_gerente')
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


#lista para el select
@role_required(allowed_roles=['admin'])
@require_http_methods(["GET"])
def gerente_list(request):
    gerentes_data = []
    for gerente in Gerente.objects.all().order_by('nombre_gerente'):
        gerentes_data.append({
            'carnet_gerente': gerente.carnet_gerente,
            'nombre_gerente': gerente.nombre_gerente,
        })
    return JsonResponse(gerentes_data, safe=False)


###########control de navios##########

#Lista de navios 
@role_required(allowed_roles=['admin'])
def gerente_list(request):
    print("DEBUG: Entrando a gerente_list. Método:", request.method) # Para depuración
    try:
        gerentes_data = []
        for gerente in Gerente.objects.all().order_by('nombre_gerente'):
            gerentes_data.append({
                'carnet_gerente': gerente.carnet_gerente, 
                'nombre_gerente': gerente.nombre_gerente,
            })
        print(f"DEBUG: Retornando {len(gerentes_data)} gerentes desde gerente_list.") 
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
        admin_logueado_carnet = request.session.get('username')

        for buque in Buque.objects.all().order_by('nombre_buque'):
            buques_data.append({
                'matricula_buque': buque.matricula_buque,
                'nombre_buque': buque.nombre_buque,
                'servicio': buque.servicio,
                'carnet_gerente': buque.carnet_gerente.carnet_gerente if buque.carnet_gerente else None,
                'administrador_logueado_en_sesion': admin_logueado_carnet,
                'carnet_admin_creador': buque.carnet_admin.carnet_admin if buque.carnet_admin else None,
            })
        return JsonResponse(buques_data, safe=False)

    elif request.method == 'POST':

        if request.session.get('user_role') != 'admin':
            return JsonResponse({'error': 'Acceso denegado. Solo los administradores pueden crear navíos.'}, status=403)

        try:
            data = json.loads(request.body)
            nombre_buque = data.get('nombre_buque')
            matricula_buque = data.get('matricula_buque')
            servicio = data.get('servicio')
            carnet_gerente_id = data.get('carnet_gerente') # Renombrado a carnet_gerente_id para mayor claridad

            if not nombre_buque or not matricula_buque:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios.'}, status=400)

            servicio_final = servicio if servicio else None

            gerente_instance = None
            if carnet_gerente_id is not None: 
                if carnet_gerente_id == "": 
                    gerente_instance = None
                else:
                    try:
                        gerente_instance = Gerente.objects.get(carnet_gerente=carnet_gerente_id)
                    except Gerente.DoesNotExist:
                        return JsonResponse({'error': f'El gerente seleccionado con Carnet "{carnet_gerente_id}" no es válido o no existe.'}, status=400)

            if Buque.objects.filter(matricula_buque=matricula_buque).exists():
                return JsonResponse({'error': f'La matrícula "{matricula_buque}" ya existe en otro navío. Por favor, ingrese una matrícula única.'}, status=409)

            admin_carnet_from_session = request.session.get('username')
            admin_instance = None
            if admin_carnet_from_session:
                try:
                    admin_instance = Administrador.objects.get(carnet_admin=admin_carnet_from_session)
                except Administrador.DoesNotExist:
                    return JsonResponse({'error': 'Administrador logueado no encontrado en el sistema.'}, status=500)

            nuevo_buque = Buque.objects.create(
                matricula_buque=matricula_buque,
                nombre_buque=nombre_buque,
                servicio=servicio_final,
                carnet_gerente=gerente_instance, 
                carnet_admin=admin_instance, 
            )
            return JsonResponse({
                'message': 'Navío creado exitosamente',
                'matricula_buque': nuevo_buque.matricula_buque,
                'nombre_buque': nuevo_buque.nombre_buque,
                'carnet_admin_creador': nuevo_buque.carnet_admin.carnet_admin if nuevo_buque.carnet_admin else None # Retornar el carnet para confirmación
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido. Verifique el formato.'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR: Error inesperado al crear buque: {e}")
            return JsonResponse({'error': f'Error interno del servidor al crear navío: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método HTTP no permitido para esta operación.'}, status=405)


#actualizacion y eliminacion de buque
@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "PUT", "DELETE"])
def buque_retrieve_update_delete(request, matricula_buque):
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)


    if request.method == 'GET':
        return JsonResponse({
            'matricula_buque': buque.matricula_buque,
            'nombre_buque': buque.nombre_buque,
            'servicio': buque.servicio,
            'carnet_gerente': buque.carnet_gerente.carnet_gerente if buque.carnet_gerente else None,
            'administrador': request.session.get('username'), # Carnet del usuario logueado en la sesión actual
            'carnet_admin_creador': buque.carnet_admin.carnet_admin if buque.carnet_admin else None, # Carnet del admin que lo creó
             
            
        })
        

    elif request.method == 'PUT':
        if request.session.get('user_role') != 'admin':
            return JsonResponse({'error': 'Acceso denegado. Solo los administradores pueden actualizar navíos.'}, status=403)

        try:
            data = json.loads(request.body)
            nombre_buque = data.get('nombre_buque', buque.nombre_buque)
            servicio = data.get('servicio', buque.servicio) # Asume que el servicio puede ser None

            nueva_matricula_buque_en_body = data.get('matricula_buque')
            if nueva_matricula_buque_en_body and nueva_matricula_buque_en_body != matricula_buque:
                return JsonResponse({'error': 'No se permite cambiar la matrícula de un navío existente. Elimine y cree uno nuevo si necesita cambiar la matrícula.'}, status=400)

            carnet_gerente_id = data.get('carnet_gerente') # Ahora es ID, por eso 'id'

            # Manejo del servicio: string vacío a None
            servicio_final = servicio if servicio else None

            # Manejo del gerente
            gerente_instance = None
            if carnet_gerente_id is not None:
                if carnet_gerente_id == "":
                    gerente_instance = None
                else:
                    try:
                        gerente_instance = Gerente.objects.get(carnet_gerente=carnet_gerente_id)
                    except Gerente.DoesNotExist:
                        return JsonResponse({'error': f'El gerente seleccionado con Carnet "{carnet_gerente_id}" no es válido o no existe.'}, status=400)
            
            buque.nombre_buque = nombre_buque
            buque.servicio = servicio_final
            buque.carnet_gerente = gerente_instance

            # Obtener y asignar la instancia del ADMINISTRADOR LOGUEADO
            admin_carnet_from_session = request.session.get('username')
            admin_instance = None
            if admin_carnet_from_session:
                try:
                    admin_instance = Administrador.objects.get(carnet_admin=admin_carnet_from_session)
                except Administrador.DoesNotExist:
                    return JsonResponse({'error': 'Administrador logueado no encontrado en el sistema.'}, status=500)
            
            buque.carnet_admin = admin_instance # ¡Asigna la instancia del objeto Administrador!
            
            buque.save()

            return JsonResponse({'message': 'Navío actualizado exitosamente', 'matricula_buque': buque.matricula_buque}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido.'}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR: Error inesperado al actualizar buque: {e}")
            return JsonResponse({'error': f'Error interno del servidor al actualizar navío: {str(e)}'}, status=500)

    elif request.method == 'DELETE':
        if request.session.get('user_role') != 'admin':
            return JsonResponse({'error': 'Acceso denegado. Solo los administradores pueden eliminar navíos.'}, status=403)
        try:
            buque.delete()
            return JsonResponse({'message': 'Navío eliminado exitosamente'}, status=204)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR: Error inesperado al eliminar buque: {e}")
            return JsonResponse({'error': f'Error interno del servidor al eliminar navío: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método HTTP no permitido para esta operación.'}, status=405)


def inventario_view(request, matricula_buque):
    return render(request, 'catalogo.html')