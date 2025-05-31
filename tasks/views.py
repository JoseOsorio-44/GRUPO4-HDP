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
        identificador_ingresado = request.POST.get('username')
        contrasenia_ingresada = request.POST.get('password')

        if not identificador_ingresado or not contrasenia_ingresada:
            return JsonResponse({'error': 'Faltan credenciales'}, status=400)

        user_role = None 
        user_obj = None 

        try:
            user_obj = Administrador.objects.get(
                identificador_admi=identificador_ingresado,
                contrasenia_admi=contrasenia_ingresada
            )
            user_role = 'admin'
        except Administrador.DoesNotExist:
            pass 

        if user_role is None: 
            try:
                user_obj = Gerente.objects.get(
                    identificador_gerente=identificador_ingresado, 
                    contrasenia_gerente=contrasenia_ingresada
                )
                user_role = 'gerente'
            except Gerente.DoesNotExist:
                return JsonResponse({'error': 'Credenciales inválidas'}, status=401)

        if user_role:
            request.session['user_id'] = user_obj.pk 
            request.session['username'] = identificador_ingresado
            request.session['user_role'] = user_role 

            # Redirigir según el rol
            if user_role == 'admin':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('completo')}, status=200)
            elif user_role == 'gerente':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('incompleto')}, status=200)

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
        # Listar todos los gerentes
        gerentes_data = []
        for gerente in Gerente.objects.all():
            gerentes_data.append({
                'id': gerente.id_gerente,
                'nombre': gerente.nombre_gerente,
                'usuario': gerente.identificador_gerente,
                'contrasenia': gerente.contrasenia_gerente,
                'email': gerente.email,
            })
        return JsonResponse(gerentes_data, safe=False) # safe=False para listas de diccionarios

    elif request.method == 'POST':
        # Crear un nuevo gerente
        try:
            # Axios envía los datos como JSON, así que usamos request.body
            data = json.loads(request.body)
            nombre = data.get('nombre')
            usuario = data.get('usuario')
            password = data.get('password')
            email = data.get('email')

            if not all([nombre, usuario, password, email]):
                return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)

            # Verificar si el usuario ya existe
            if Gerente.objects.filter(identificador_gerente=usuario).exists():
                return JsonResponse({'error': 'El nombre de usuario ya existe'}, status=409)

            
            max_id = Gerente.objects.all().order_by('-id_gerente').first()
            new_id = (max_id.id_gerente + 1) if max_id else 1

            # Si quieres usar hashing de contraseñas para Gerente:
            # hashed_password = make_password(password)

            nuevo_gerente = Gerente.objects.create(
                id_gerente=new_id, # Comenta/ajusta si ID_GERENTE es SERIAL
                nombre_gerente=nombre,
                identificador_gerente=usuario,
                contrasenia_gerente=password, 
                # contrasenia_gerente=hashed_password, # Con hashing (RECOMENDADO)
                email=email,
                # id_buque: aquí tendrías que definir cómo se asigna el buque si es necesario
            )
            return JsonResponse({'message': 'Gerente creado exitosamente', 'id': nuevo_gerente.id_gerente}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
        
@role_required(allowed_roles=['admin'])    
@require_http_methods(["PUT", "DELETE"]) # Añadido DELETE si lo vas a implementar
def gerente_retrieve_update(request, gerente_id):
    gerente = get_object_or_404(Gerente, id_gerente=gerente_id)

    if request.method == 'PUT':
        # Actualizar un gerente
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre')
            usuario = data.get('usuario')
            password = data.get('password') # Puede ser opcional en PUT si no se cambia
            email = data.get('email')

            if not all([nombre, usuario, email]): # Password puede ser opcional
                return JsonResponse({'error': 'Faltan campos obligatorios para actualizar'}, status=400)

            # Verificar si el nuevo usuario ya existe para otro gerente
            if Gerente.objects.filter(identificador_gerente=usuario).exclude(id_gerente=gerente_id).exists():
                return JsonResponse({'error': 'El nombre de usuario ya está en uso por otro gerente'}, status=409)

            gerente.nombre_gerente = nombre
            gerente.identificador_gerente = usuario
            if password: # Solo actualiza la contraseña si se proporcionó una nueva
                # Si usas hashing: gerente.contrasenia_gerente = make_password(password)
                gerente.contrasenia_gerente = password # Sin hashing
            gerente.email = email
            gerente.save()

            return JsonResponse({'message': 'Gerente actualizado exitosamente'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        # Eliminar un gerente (si lo vas a implementar)
        try:
            gerente.delete()
            return JsonResponse({'message': 'Gerente eliminado exitosamente'}, status=204) # 204 No Content
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@role_required(allowed_roles=['admin'])    
def ver_navios(request):
    return render(request, 'navio.html')


@role_required(allowed_roles=['admin'])
@require_http_methods(["GET"])
def gerente_list(request):
    gerentes_data = []
    for gerente in Gerente.objects.all().order_by('nombre_gerente'):
        gerentes_data.append({
            'id_gerente': gerente.id_gerente,
            'nombre_gerente': gerente.nombre_gerente,
        })
    return JsonResponse(gerentes_data, safe=False)


########################################################################


@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "POST"])
def buque_list_create(request):
    if request.method == 'GET':
        buques_data = []
        for buque in Buque.objects.all().order_by('nombre_buque'):
            buques_data.append({
                'id_buque': buque.id_buque,
                'nombre_buque': buque.nombre_buque,
                'matricula': buque.matricula,
                'servicio': buque.servicio, 
                'gerente': buque.id_gerente.id_gerente if buque.id_gerente else None, # Usa id_gerente
                'administrador': None, # Siempre None en la respuesta GET para este campo
            })
        return JsonResponse(buques_data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_buque = data.get('nombre_buque')
            matricula = data.get('matricula')
            servicio = data.get('servicio') 
            gerente_id = data.get('gerente') 
            
            if not nombre_buque or not matricula:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios.'}, status=400)
            
            servicio = servicio if servicio else None 
            gerente_id = gerente_id if gerente_id else None 

            gerente_instance = None
            if gerente_id is not None: 
                try:
                    gerente_instance = Gerente.objects.get(id_gerente=int(gerente_id)) 
                except (Gerente.DoesNotExist, ValueError): 
                    return JsonResponse({'error': f'El gerente seleccionado con ID "{gerente_id}" no es válido o no existe.'}, status=400)
        
            
            if Buque.objects.filter(matricula=matricula).exists():
                return JsonResponse({'error': f'La matrícula "{matricula}" ya existe en otro navío. Por favor, ingrese una matrícula única.'}, status=409)

            max_id = Buque.objects.all().order_by('-id_buque').first()
            new_id = (max_id.id_buque + 1) if max_id else 1

            nuevo_buque = Buque.objects.create(
                id_buque=new_id,
                nombre_buque=nombre_buque,
                matricula=matricula,
                servicio=servicio,
                id_gerente=gerente_instance, # Usar 'id_gerente' si ese es el nombre del campo ForeignKey
                id_administrador=None, # **CORREGIDO: Usar el nombre del campo 'id_administrador' y pasar None**
            )
            return JsonResponse({
                'message': 'Navío creado exitosamente',
                'id_buque': nuevo_buque.id_buque,
                'nombre_buque': nuevo_buque.nombre_buque,
                'matricula': nuevo_buque.matricula,
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
def buque_retrieve_update_delete(request, id_buque):
    buque = get_object_or_404(Buque, id_buque=id_buque)

    if request.method == 'GET':
        return JsonResponse({
            'id_buque': buque.id_buque,
            'nombre_buque': buque.nombre_buque,
            'matricula': buque.matricula,
            'servicio': buque.servicio,
            'gerente': buque.id_gerente.id_gerente if buque.id_gerente else None,
            'administrador': None, # Siempre None en la respuesta GET según tu lógica
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nombre_buque = data.get('nombre_buque')
            matricula = data.get('matricula')
            servicio = data.get('servicio')
            gerente_id = data.get('gerente')

            if not nombre_buque or not matricula:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios para actualizar.'}, status=400)

            servicio = servicio if servicio else None
            gerente_id = gerente_id if gerente_id else None

            gerente_instance = None
            if gerente_id is not None:
                try:
                    gerente_instance = Gerente.objects.get(id_gerente=int(gerente_id))
                except (Gerente.DoesNotExist, ValueError):
                    return JsonResponse({'error': f'El gerente seleccionado con ID "{gerente_id}" no es válido o no existe.'}, status=400)

            if Buque.objects.filter(matricula=matricula).exclude(id_buque=id_buque).exists():
                return JsonResponse({'error': f'La matrícula "{matricula}" ya está en uso por otro navío. Por favor, ingrese una matrícula única.'}, status=409)

            buque.nombre_buque = nombre_buque
            buque.matricula = matricula
            buque.servicio = servicio
            buque.id_gerente = gerente_instance
            buque.id_administrador = None
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