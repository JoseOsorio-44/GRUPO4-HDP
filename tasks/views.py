from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from tasks.models import Administrador, Gerente, Buque, Producto
from django.contrib import messages
from django.urls import reverse
from .decorator import role_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import traceback
import os
from datetime import datetime


def home(request):
    return render(request, 'home.html')


def login(request):
    return render(request, 'login.html')


#filtrado de usuario
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


#vista de administrador
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    carnet_admin_logueado = request.session.get('username')
    rol_logueado = request.session.get('user_role')
    return render(request, 'gerente.html', {
        'username': carnet_admin_logueado,
        'role': rol_logueado
    })


#vista de gerente
@role_required(allowed_roles=['gerente'])
def gerente_dashboard(request):
    carnet_gerente_logueado = request.session.get('username')
    rol_logueado = request.session.get('user_role')
    matricula_buque_asociada = request.session.get('buque_matricula')
    return render(request, 'incompleto.html', {
        'username': carnet_gerente_logueado,
        'role': rol_logueado,
        'buque_matricula': matricula_buque_asociada
    })


#vista de sin permisos
def sin_permisos(request):
    return render(request, 'sinpermiso.html', {
        'message': 'No tienes los permisos necesarios para acceder a esta sección.',
        'username': request.session.get('username', 'Invitado')
    })


#cierre de sesion
def logout_view(request):
    request.session.flush()
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect(reverse('login'))


#vista de lista de gerentes y creacion
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


#delete y update de gerentes
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


#vista de navios
@role_required(allowed_roles=['admin'])
def ver_navios(request):
    return render(request, 'navio.html')


#creacion de lista y de buque
@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "POST"])
def buque_list_create(request):
    if request.method == 'GET':
        buques_data = []
        admin_logueado_carnet = request.session.get('username')

        for buque in Buque.objects.all().order_by('nombre_buque'):
            nombre_gerente_asignado = buque.carnet_gerente.nombre_gerente if buque.carnet_gerente else None

            buques_data.append({
                'matricula_buque': buque.matricula_buque,
                'nombre_buque': buque.nombre_buque,
                'servicio': buque.servicio,
                'carnet_gerente': buque.carnet_gerente.carnet_gerente if buque.carnet_gerente else None,
                'nombre_gerente_asignado': nombre_gerente_asignado,
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
            carnet_gerente_id = data.get('carnet_gerente')

            if not nombre_buque or not matricula_buque:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios.'}, status=400)

            servicio_final = servicio if servicio else None

            gerente_instance = None
            if carnet_gerente_id is not None and carnet_gerente_id != "":
                try:
                    gerente_instance = Gerente.objects.get(carnet_gerente=carnet_gerente_id)
                    if gerente_instance.matricula_buque is not None:
                        return JsonResponse({'error': f'El gerente "{gerente_instance.nombre_gerente}" (Carnet: {gerente_instance.carnet_gerente}) ya está asignado a otro navío y no puede ser seleccionado.'}, status=400)
                except Gerente.DoesNotExist:
                    return JsonResponse({'error': f'El gerente seleccionado con Carnet "{carnet_gerente_id}" no es válido o no existe.'}, status=400)

            if Buque.objects.filter(matricula_buque=matricula_buque).exists():
                return JsonResponse({'error': f'La matrícula "{matricula_buque}" ya existe en el sistema'}, status=409)

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

            if gerente_instance:
                gerente_instance.matricula_buque = nuevo_buque
                gerente_instance.save()

            return JsonResponse({
                'message': 'Navío creado exitosamente',
                'matricula_buque': nuevo_buque.matricula_buque,
                'nombre_buque': nuevo_buque.nombre_buque,
                'carnet_admin_creador': nuevo_buque.carnet_admin.carnet_admin if nuevo_buque.carnet_admin else None
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido. Verifique el formato.'}, status=400)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'error': f'{str(e)}'}, status=500)

    return JsonResponse({'error': 'Método HTTP no permitido para esta operación.'}, status=405)


#update y delete de buque
@role_required(allowed_roles=['admin'])
@require_http_methods(["PUT", "DELETE"])
@csrf_exempt
def buque_retrieve_update_delete(request, matricula_buque):
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)

    if request.method == 'PUT':
        if request.session.get('user_role') != 'admin':
            return JsonResponse({'error': 'Acceso denegado. Solo los administradores pueden actualizar navíos.'}, status=403)

        try:
            data = json.loads(request.body)
            nuevo_nombre_buque = data.get('nombre_buque')
            nuevo_matricula_buque = data.get('matricula_buque')
            nuevo_servicio = data.get('servicio')
            nuevo_carnet_gerente_id = data.get('carnet_gerente')

            if not nuevo_nombre_buque or not nuevo_matricula_buque:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios.'}, status=400)

            if Buque.objects.filter(matricula_buque=nuevo_matricula_buque).exclude(matricula_buque=matricula_buque).exists():
                return JsonResponse({'error': f'La matrícula "{nuevo_matricula_buque}" ya existe en otro navío. Por favor, ingrese una matrícula única.'}, status=409)

            old_gerente = buque.carnet_gerente
            if old_gerente and (nuevo_carnet_gerente_id is None or nuevo_carnet_gerente_id == "" or str(old_gerente.carnet_gerente) != str(nuevo_carnet_gerente_id)):
                old_gerente.matricula_buque = None
                old_gerente.save()

            new_gerente_instance = None
            if nuevo_carnet_gerente_id is not None and nuevo_carnet_gerente_id != "":
                try:
                    new_gerente_instance = Gerente.objects.get(carnet_gerente=nuevo_carnet_gerente_id)
                    if new_gerente_instance.matricula_buque is not None and new_gerente_instance.matricula_buque.matricula_buque != buque.matricula_buque:
                        return JsonResponse({'error': f'El gerente "{new_gerente_instance.nombre_gerente}" (Carnet: {new_gerente_instance.carnet_gerente}) ya está asignado a otro navío y no puede ser seleccionado.'}, status=400)
                except Gerente.DoesNotExist:
                    return JsonResponse({'error': f'El gerente seleccionado con Carnet "{nuevo_carnet_gerente_id}" no es válido o no existe.'}, status=400)

            buque.nombre_buque = nuevo_nombre_buque
            buque.matricula_buque = nuevo_matricula_buque
            buque.servicio = nuevo_servicio if nuevo_servicio else None
            buque.carnet_gerente = new_gerente_instance
            buque.save()

            if new_gerente_instance:
                new_gerente_instance.matricula_buque = buque
                new_gerente_instance.save()

            return JsonResponse({'message': 'Navío actualizado correctamente'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido.'}, status=400)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'error': f'{str(e)}'}, status=500)

    elif request.method == 'DELETE':
        if request.session.get('user_role') != 'admin':
            return JsonResponse({'error': 'Acceso denegado. Solo los administradores pueden eliminar navíos.'}, status=403)
        try:
            if buque.carnet_gerente:
                gerente_asociado = buque.carnet_gerente
                gerente_asociado.matricula_buque = None
                gerente_asociado.save()

            buque.delete()
            return JsonResponse({'message': 'Navío eliminado correctamente'}, status=204)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'error': f'Error interno del servidor al eliminar navío: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método HTTP no permitido.'}, status=405)


#lista de gerentes para select
@role_required(allowed_roles=['admin'])
@require_http_methods(["GET"])
def gerente_list(request):
    try:
        gerentes_qs = Gerente.objects.filter(matricula_buque__isnull=True).order_by('nombre_gerente')
        gerentes_data = []
        for gerente in gerentes_qs:
            gerentes_data.append({
                'carnet_gerente': gerente.carnet_gerente,
                'nombre_gerente': gerente.nombre_gerente,
                'matricula_buque': gerente.matricula_buque.matricula_buque if gerente.matricula_buque else None
            })
        return JsonResponse(gerentes_data, safe=False)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': f'Error interno del servidor en gerente_list: {str(e)}'}, status=500)




@role_required(allowed_roles=['admin', 'gerente'])
@require_http_methods(["GET", "POST"])
@csrf_exempt
def producto_list_create(request):
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





def catalogo_view(request, matricula_buque):
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)
    productos = Producto.objects.filter(matricula_buque=buque)
    return render(request, 'catalogo.html', {'buque': buque, 'productos': productos})




@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_productos_list_create(request, matricula_buque):
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)

    if request.method == 'GET':
        productos = Producto.objects.filter(matricula_buque=buque).order_by('nombre_producto')
        data = []
        for producto in productos:
            data.append({
                'id_producto': producto.id_producto.strip() if producto.id_producto else None, # Asegurar que el ID se limpia al enviar
                'nombre_producto': producto.nombre_producto,
                'descripcion': producto.descripcion,
                'cantidad': producto.cantidad,
                'stock_minimo': producto.stock_minimo,
                'tipo': producto.tipo,
                'fecha_caducidad': producto.fecha_caducidad.strftime('%Y-%m-%d') if producto.fecha_caducidad else None,
                'imagen_url': producto.foto_producto.url if producto.foto_producto else None,
            })
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else: # Asumimos FormData
                data = request.POST.dict()

            id_producto = data.get('id_producto')
            if id_producto:
                id_producto = id_producto.strip() # <<< CRÍTICO: Recortar espacios para la creación

            nombre_producto = data.get('nombre_producto')
            cantidad = data.get('cantidad')
            stock_minimo = data.get('stock_minimo')
            tipo = data.get('tipo')
            descripcion = data.get('descripcion')
            fecha_caducidad = data.get('fecha_caducidad')

            if not all([id_producto, nombre_producto, cantidad, stock_minimo, tipo]):
                return JsonResponse({'errors': {'general': ['Faltan campos obligatorios.']}}, status=400)

            if Producto.objects.filter(matricula_buque=buque, id_producto=id_producto).exists():
                return JsonResponse({'errors': {'id_producto': ['El código de producto ya existe para este buque.']}}, status=400)

            if tipo == 'provision' and not fecha_caducidad:
                return JsonResponse({'errors': {'fecha_caducidad': ['La fecha de caducidad es obligatoria para las provisiones.']}}, status=400)

            new_producto = Producto(
                matricula_buque=buque,
                id_producto=id_producto,
                nombre_producto=nombre_producto,
                descripcion=descripcion,
                cantidad=cantidad,
                stock_minimo=stock_minimo,
                tipo=tipo,
                fecha_caducidad=fecha_caducidad if fecha_caducidad else None,
            )
            
            if 'foto_producto' in request.FILES:
                new_producto.foto_producto = request.FILES['foto_producto']

            new_producto.save()
            return JsonResponse({'message': 'Producto creado exitosamente'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON or FormData'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_producto_detail_update_delete(request, matricula_buque, id_producto):
    id_producto = id_producto.strip() 
    
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)
    producto = get_object_or_404(Producto, matricula_buque=buque, id_producto=id_producto)

    if request.method == 'POST' and request.POST.get('_method') == 'PUT':
        try:
            data = request.POST.dict()

            producto.nombre_producto = data.get('nombre_producto', producto.nombre_producto)
            producto.descripcion = data.get('descripcion', producto.descripcion)
            producto.cantidad = data.get('cantidad', producto.cantidad)
            producto.stock_minimo = data.get('stock_minimo', producto.stock_minimo)
            producto.tipo = data.get('tipo', producto.tipo) # Asigna el valor entrante directamente

            fecha_caducidad_str = data.get('fecha_caducidad')
            if producto.tipo == 'provision' and not fecha_caducidad_str:
                return JsonResponse({'errors': {'fecha_caducidad': ['La fecha de caducidad es obligatoria para provisiones.']}}, status=400)
            producto.fecha_caducidad = fecha_caducidad_str if fecha_caducidad_str else None

            if 'foto_producto' in request.FILES:
                if producto.foto_producto:
                    try:
                        old_image_path = producto.foto_producto.path
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except ValueError:
                        pass
                    except Exception as e:
                        print(f"Error al intentar eliminar imagen antigua: {e}")
                producto.foto_producto = request.FILES['foto_producto']
            elif 'foto_producto' in data and data['foto_producto'] == '':
                if producto.foto_producto:
                    try:
                        old_image_path = producto.foto_producto.path
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except ValueError:
                        pass
                    except Exception as e:
                        print(f"Error al intentar eliminar imagen por checkbox: {e}")
                producto.foto_producto = None
            
            # producto.full_clean() # Descomenta si quieres activar la validación completa del modelo
            producto.save()
            return JsonResponse({'message': 'Producto actualizado exitosamente'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST' and request.POST.get('_method') == 'DELETE':
        try:
            if producto.foto_producto:
                try:
                    image_path = producto.foto_producto.path
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except ValueError:
                    pass
                except Exception as e:
                    print(f"Error al intentar eliminar imagen al borrar producto: {e}")

            producto.delete()
            return JsonResponse({'message': 'Producto eliminado exitosamente'}, status=204)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST': # Manejo de creación de producto (POST sin _method=PUT/DELETE)
        try:
            data = request.POST.dict()
            files = request.FILES
            
            id_producto_nuevo = data.get('id_producto')
            if not id_producto_nuevo:
                return JsonResponse({'errors': {'id_producto': ['El código del producto es obligatorio.']}}, status=400)

            if Producto.objects.filter(matricula_buque=buque, id_producto=id_producto_nuevo).exists():
                return JsonResponse({'errors': {'id_producto': ['Ya existe un producto con este código para este buque.']}}, status=400)

            nuevo_producto = Producto(
                matricula_buque=buque,
                id_producto=id_producto_nuevo,
                nombre_producto=data.get('nombre_producto'),
                descripcion=data.get('descripcion'),
                cantidad=data.get('cantidad'),
                stock_minimo=data.get('stock_minimo'),
                tipo=data.get('tipo'), # Asigna el valor directamente
            )

            fecha_caducidad_str = data.get('fecha_caducidad')
            if nuevo_producto.tipo == 'provision' and not fecha_caducidad_str:
                return JsonResponse({'errors': {'fecha_caducidad': ['La fecha de caducidad es obligatoria para provisiones.']}}, status=400)
            nuevo_producto.fecha_caducidad = fecha_caducidad_str if fecha_caducidad_str else None

            if 'foto_producto' in files:
                nuevo_producto.foto_producto = files['foto_producto']

            # nuevo_producto.full_clean() # Descomenta si quieres activar la validación completa del modelo
            nuevo_producto.save()
            return JsonResponse({'message': 'Producto creado exitosamente'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'GET':
        producto_data = {
            'id_producto': producto.id_producto,
            'nombre_producto': producto.nombre_producto,
            'descripcion': producto.descripcion,
            'cantidad': producto.cantidad,
            'stock_minimo': producto.stock_minimo,
            'tipo': producto.tipo,
            'fecha_caducidad': producto.fecha_caducidad.strftime('%Y-%m-%d') if producto.fecha_caducidad else None,
            'imagen_url': producto.foto_producto.url if producto.foto_producto else None,
        }
        return JsonResponse(producto_data)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
