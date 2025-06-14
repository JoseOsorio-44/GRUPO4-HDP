from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from tasks.models import Administrador, Gerente, Buque, Producto
from tasks.decorator import role_required
from django.views.decorators.http import require_http_methods
import json
import traceback
import os

#vista de administrador
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    carnet_admin_logueado = request.session.get('username')
    rol_logueado = request.session.get('user_role')
    return render(request, 'gerentes.html', {
        'username': carnet_admin_logueado,
        'role': rol_logueado
    })


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
    return render(request, 'buques.html')


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
@require_http_methods(["GET", "PUT", "DELETE"]) 
def buque_retrieve_update_delete(request, matricula_buque):
    matricula_buque_cleaned = matricula_buque.strip() 

    try:
        buque = get_object_or_404(Buque, matricula_buque=matricula_buque_cleaned)
    except Exception as e:
        print(f"Error al buscar buque {matricula_buque_cleaned}: {e}")
        return JsonResponse({'error': 'Navío no encontrado o error en la búsqueda.'}, status=404)


    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nuevo_nombre_buque = data.get('nombre_buque')
            nuevo_matricula_buque = data.get('matricula_buque')
            nuevo_servicio = data.get('servicio')
            nuevo_carnet_gerente_id = data.get('carnet_gerente')

            if not nuevo_nombre_buque or not nuevo_matricula_buque:
                return JsonResponse({'error': 'El nombre del navío y la matrícula son obligatorios.'}, status=400)

            if Buque.objects.filter(matricula_buque=nuevo_matricula_buque).exclude(matricula_buque=matricula_buque_cleaned).exists():
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
        try:

            productos_eliminados_count, _ = Producto.objects.filter(matricula_buque=buque).delete()
            print(f"DEBUG: Se eliminaron {productos_eliminados_count} productos asociados al navío {buque.matricula_buque}.")

            if buque.carnet_gerente:
                gerente_asociado = buque.carnet_gerente
                gerente_asociado.matricula_buque = None
                gerente_asociado.save()

            buque.delete()
            return JsonResponse({'message': 'Navío y productos asociados eliminados correctamente'}, status=204)
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'error': f'Error interno del servidor al eliminar navío: {str(e)}'}, status=500)

    elif request.method == 'GET':
        # Retorna los datos del buque
        buque_data = {
            'matricula_buque': buque.matricula_buque,
            'nombre_buque': buque.nombre_buque,
            'servicio': buque.servicio,
            'carnet_gerente': buque.carnet_gerente.carnet_gerente if buque.carnet_gerente else None,
            'nombre_gerente_asignado': buque.carnet_gerente.nombre if buque.carnet_gerente else None,
        }
        return JsonResponse(buque_data)

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




@role_required(allowed_roles=['admin'])
def catalogo_view(request, matricula_buque):
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)
    productos = Producto.objects.filter(matricula_buque=buque)
    return render(request, 'catalogo_admin.html', {'buque': buque, 'productos': productos})

@role_required(allowed_roles=['admin'])
@require_http_methods(["POST"])
def api_administrador_create(request):
    try:
        data = request.POST.dict()
        print(f"DEBUG VIEWS (Administrador): Datos recibidos para creación: {data}")

        carnet_admin = data.get('carnet_admin', '').strip()
        nombre_admin = data.get('nombre_admin', '').strip()
        password_admin = data.get('password_admin', '')

        if not carnet_admin:
            return JsonResponse({'errors': {'carnet_admin': ['El carnet del administrador es obligatorio.']}}, status=400)
        if not nombre_admin:
            return JsonResponse({'errors': {'nombre_admin': ['El nombre del administrador es obligatorio.']}}, status=400)
        if not password_admin:
            return JsonResponse({'errors': {'password_admin': ['La contraseña es obligatoria.']}}, status=400)
        
        if len(carnet_admin) > 8:
            return JsonResponse({'errors': {'carnet_admin': ['El carnet no puede exceder los 8 caracteres.']}}, status=400)
        if len(nombre_admin) > 30:
            return JsonResponse({'errors': {'nombre_admin': ['El nombre no puede exceder los 30 caracteres.']}}, status=400)
        if len(password_admin) > 15:
            return JsonResponse({'errors': {'password_admin': ['La contraseña no puede exceder los 15 caracteres.']}}, status=400)


        if Administrador.objects.filter(carnet_admin=carnet_admin).exists():
            print(f"DEBUG VIEWS (Administrador): Intento de crear administrador con carnet duplicado: {carnet_admin}")
            return JsonResponse({'errors': {'carnet_admin': ['Ya existe un administrador con este carnet.']}}, status=400)

        nuevo_administrador = Administrador(
            carnet_admin=carnet_admin,
            nombre_admin=nombre_admin,
            password_admin=password_admin 
        )
        
        nuevo_administrador.save()
        print(f"DEBUG VIEWS (Administrador): Administrador '{carnet_admin}' creado exitosamente.")
        return JsonResponse({'message': 'Administrador creado exitosamente'}, status=201)

    except Exception as e:
        print(f"ERROR VIEWS (Administrador): Error en la creación del administrador: {e}")
        # Puedes añadir más detalle si es un ValidationError de Django
        return JsonResponse({'error': str(e)}, status=500)





@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "POST"])
def api_productos_list_create(request, matricula_buque):
    # Asegúrate de que la matrícula del buque de la URL también se limpia
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque.strip())

    if request.method == 'GET':
        productos = Producto.objects.filter(matricula_buque=buque).order_by('nombre_producto')
        data = []
        for producto in productos:
            foto_url = None
            if producto.foto_producto:
                foto_url = request.build_absolute_uri(producto.foto_producto.url).strip()

            data.append({
                'codigo_producto': producto.codigo_producto.strip(),
                'nombre_producto': producto.nombre_producto.strip(),
                'descripcion': producto.descripcion.strip() if producto.descripcion else '',
                'cantidad': producto.cantidad,
                'stock_minimo': producto.stock_minimo,
                'tipo': producto.tipo.strip(),
                'fecha_caducidad': producto.fecha_caducidad.strftime('%Y-%m-%d') if producto.fecha_caducidad else None,
                'imagen_url': foto_url,
                'medida': producto.medida.strip() if producto.medida else '', # Aseguramos que 'medida' también se limpie
            })
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            data = request.POST.dict()
            files = request.FILES

            incoming_codigo_producto = data.get('codigo_producto', '').strip()
            nombre_producto = data.get('nombre_producto', '').strip()
            cantidad = data.get('cantidad')
            stock_minimo = data.get('stock_minimo')
            tipo = data.get('tipo', '').strip()
            descripcion = data.get('descripcion', '').strip() # Aseguramos que descripción también se limpie
            fecha_caducidad = data.get('fecha_caducidad') # No es string, no necesita strip
            medida = data.get('medida', '').strip() 

            if not all([incoming_codigo_producto, nombre_producto, cantidad, stock_minimo, tipo, medida]):
                return JsonResponse({'errors': {'general': ['Faltan campos obligatorios (incluyendo Código de Producto y Medida).']}}, status=400)

            if Producto.objects.filter(codigo_producto=incoming_codigo_producto).exists():
                return JsonResponse({'errors': {'codigo_producto': ['Ya existe un producto con este código.']}}, status=400)

            if tipo == 'provision' and not fecha_caducidad:
                return JsonResponse({'errors': {'fecha_caducidad': ['La fecha de caducidad es obligatoria para las provisiones.']}}, status=400)

            admin_username = request.session.get('username').strip()
            admin_instance = None
            if admin_username:
                try:
                    admin_instance = Administrador.objects.get(carnet_admin=admin_username)
                except Administrador.DoesNotExist:
                    return JsonResponse({'error': f'Administrador con carnet "{admin_username}" no encontrado.'}, status=400)
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

            new_producto = Producto(
                codigo_producto=incoming_codigo_producto,
                matricula_buque=buque,
                nombre_producto=nombre_producto,
                descripcion=descripcion,
                cantidad=cantidad,
                stock_minimo=stock_minimo,
                tipo=tipo,
                fecha_caducidad=fecha_caducidad if fecha_caducidad else None,
                carnet_admin=admin_instance,
                medida=medida,
            )

            if 'foto_producto' in files:
                new_producto.foto_producto = files['foto_producto']
            else:
                new_producto.foto_producto = None

            new_producto.save()
            return JsonResponse({'message': 'Producto creado exitosamente'}, status=201)

        except Exception as e:
            print(f"Error al crear producto: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@role_required(allowed_roles=['admin'])
@require_http_methods(["GET", "POST"])
def api_producto_detail_update_delete(request, matricula_buque, codigo_producto_url):
    buque = get_object_or_404(Buque, matricula_buque=matricula_buque)
    producto = get_object_or_404(Producto, codigo_producto=codigo_producto_url.strip())

    if request.method == 'POST' and request.POST.get('_method') == 'PUT':
        try:
            data = request.POST.dict()

            nombre_producto = data.get('nombre_producto', producto.nombre_producto).strip()
            descripcion = data.get('descripcion', producto.descripcion).strip()
            cantidad = data.get('cantidad', producto.cantidad)
            stock_minimo = data.get('stock_minimo', producto.stock_minimo)
            fecha_caducidad = data.get('fecha_caducidad')
            eliminar_imagen = data.get('eliminar_imagen_checkbox') == 'true'

            # No se actualiza 'tipo' ni 'medida' en esta vista, se mantienen como estaban
            # ya que la lógica lo requiere como lectura para la edición.

            if not all([nombre_producto, cantidad, stock_minimo]):
                return JsonResponse({'errors': {'general': ['Faltan campos obligatorios para actualizar.']}}, status=400)

            if producto.tipo == 'provision' and not fecha_caducidad:
                return JsonResponse({'errors': {'fecha_caducidad': ['La fecha de caducidad es obligatoria para provisiones.']}}, status=400)

            admin_username = request.session.get('username')
            admin_instance = None
            if admin_username:
                try:
                    admin_instance = Administrador.objects.get(carnet_admin=admin_username)
                except Administrador.DoesNotExist:
                    return JsonResponse({'error': f'Administrador con carnet "{admin_username}" no encontrado para la actualización.'}, status=400)
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

            producto.nombre_producto = nombre_producto
            producto.descripcion = descripcion
            producto.cantidad = cantidad
            producto.stock_minimo = stock_minimo
            producto.fecha_caducidad = fecha_caducidad if fecha_caducidad else None
            producto.carnet_admin = admin_instance

            if eliminar_imagen:
                if producto.foto_producto:
                    try:
                        old_image_path = producto.foto_producto.path
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except ValueError:
                        pass
                    except Exception as e:
                        pass
                producto.foto_producto = None
            elif 'foto_producto' in request.FILES:
                if producto.foto_producto:
                    try:
                        old_image_path = producto.foto_producto.path
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except ValueError:
                        pass
                    except Exception as e:
                        pass
                producto.foto_producto = request.FILES['foto_producto']
            elif not request.FILES and not eliminar_imagen:
                pass
            
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
                    pass

            producto.delete()
            return JsonResponse({'message': 'Producto eliminado exitosamente'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'GET':
        producto_data = {
            'codigo_producto': producto.codigo_producto,
            'nombre_producto': producto.nombre_producto,
            'descripcion': producto.descripcion,
            'cantidad': producto.cantidad,
            'stock_minimo': producto.stock_minimo,
            'tipo': producto.tipo,
            'fecha_caducidad': producto.fecha_caducidad.strftime('%Y-%m-%d') if producto.fecha_caducidad else None,
            'imagen_url': producto.foto_producto.url if producto.foto_producto else None,
            'medida': producto.medida, 
        }
        return JsonResponse(producto_data)

    return JsonResponse({'error': 'Método no permitido'}, status=405)