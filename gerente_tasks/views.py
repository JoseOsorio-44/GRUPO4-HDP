from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from tasks.models import  Buque, Producto
from tasks.decorator import role_required
from django.views.decorators.http import require_http_methods
import json


@role_required(allowed_roles=['gerente'])
def gerente_dashboard(request):

    carnet_gerente_logueado = request.session.get('username')
    rol_logueado = request.session.get('user_role')
    matricula_buque_asociada = request.session.get('buque_matricula')

    nombre_buque_display = "Buque no encontrado"
    if not matricula_buque_asociada:
        return render(request, 'sin_navio.html')
    try:
        buque = Buque.objects.get(matricula_buque=matricula_buque_asociada.strip()) # <--- .strip() aquí
        nombre_buque_display = buque.nombre_buque
    except Buque.DoesNotExist:
        # Si el buque no existe en la base de datos, aunque la matrícula esté en sesión
        return HttpResponse("El buque asociado a tu sesión no existe en la base de datos. Por favor, contacta a un administrador.", status=404)

    context = {
        'username': carnet_gerente_logueado,
        'role': rol_logueado,
        'matricula_buque': matricula_buque_asociada.strip(), # <--- .strip() aquí
        'nombre_buque': nombre_buque_display,
    }
    return render(request, 'catalogo_gerente.html', context)



@role_required(allowed_roles=['gerente'])
@require_http_methods(["GET"])
def api_productos_gerente_list(request):
    """
    API para obtener la lista de productos que coinciden con la matricula_buque
    del gerente logueado.
    """
    matricula_buque_gerente = request.session.get('buque_matricula')
    
    if not matricula_buque_gerente:
        return JsonResponse({'error': 'Matrícula de buque no encontrada en la sesión.'}, status=403)

    try:
        # Asegúrate de que la matrícula usada para la consulta no tenga espacios
        buque = Buque.objects.get(matricula_buque=matricula_buque_gerente.strip()) # <--- .strip() aquí
    except Buque.DoesNotExist:
        return JsonResponse({'error': 'El buque asociado no existe.'}, status=404)

    productos = Producto.objects.filter(matricula_buque=buque).order_by('nombre_producto')
    
    productos_data = []
    for producto in productos:
        foto_url = None
        if producto.foto_producto:
            # Asegura que la URL de la imagen no tenga espacios extra
            foto_url = request.build_absolute_uri(producto.foto_producto.url).strip() # <--- .strip() aquí
            
        productos_data.append({
            'codigo_producto': producto.codigo_producto.strip(), # <--- .strip() aquí
            'nombre_producto': producto.nombre_producto.strip(), # <--- .strip() aquí
            'tipo': producto.tipo.strip(), # <--- .strip() aquí
            'cantidad': producto.cantidad,
            'stock_minimo': producto.stock_minimo,
            'fecha_caducidad': producto.fecha_caducidad.strftime('%Y-%m-%d') if producto.fecha_caducidad else None,
            'foto_producto_url': foto_url
        })
        
    return JsonResponse(productos_data, safe=False)


@role_required(allowed_roles=['gerente'])
@require_http_methods(["GET"])
def api_producto_gerente_detail(request, codigo_producto):
    """
    API para obtener los detalles de un producto específico,
    verificando que pertenece al buque del gerente logueado.
    """
    matricula_buque_gerente = request.session.get('buque_matricula')
    
    if not matricula_buque_gerente:
        return JsonResponse({'error': 'Matrícula de buque no encontrada en la sesión.'}, status=403)

    # Asegúrate de que el código de producto de la URL y la matrícula de la sesión no tengan espacios
    producto = get_object_or_404(
        Producto, 
        codigo_producto=codigo_producto.strip(), # <--- .strip() aquí
        matricula_buque__matricula_buque=matricula_buque_gerente.strip() # <--- .strip() aquí
    )

    foto_url = None
    if producto.foto_producto:
        # Asegura que la URL de la imagen no tenga espacios extra
        foto_url = request.build_absolute_uri(producto.foto_producto.url).strip() # <--- .strip() aquí

    producto_data = {
        'codigo_producto': producto.codigo_producto.strip(),
        'nombre_producto': producto.nombre_producto.strip(),
        'descripcion': producto.descripcion.strip() if producto.descripcion else '', # <--- .strip() y manejar None
        'cantidad': producto.cantidad,
        'stock_minimo': producto.stock_minimo, 
        'tipo': producto.tipo.strip(),
        'fecha_caducidad': producto.fecha_caducidad.strftime('%Y-%m-%d') if producto.fecha_caducidad else None,
        'foto_producto_url': foto_url,
    }
    return JsonResponse(producto_data)


@role_required(allowed_roles=['gerente'])
@require_http_methods(["PUT"])
def api_producto_gerente_update_cantidad(request, codigo_producto):
    """
    API para actualizar solo la cantidad de un producto.
    Permite reducir la cantidad pero NO aumentarla.
    """
    matricula_buque_gerente = request.session.get('buque_matricula')
    
    if not matricula_buque_gerente:
        return JsonResponse({'error': 'Matrícula de buque no encontrada en la sesión.'}, status=403)

    producto = get_object_or_404(
        Producto, 
        codigo_producto=codigo_producto.strip(), # <--- .strip() aquí
        matricula_buque__matricula_buque=matricula_buque_gerente.strip() # <--- .strip() aquí
    )
    
    try:
        data = json.loads(request.body)
        new_cantidad = int(data.get('cantidad'))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Cantidad no válida proporcionada.'}, status=400)

    # Validación de cantidad: NO se puede aumentar
    if new_cantidad > producto.cantidad:
        return JsonResponse({'error': f'No se puede aumentar la cantidad de {producto.nombre_producto.strip()} (actual: {producto.cantidad}).'}, status=400)
    
    # Validación de cantidad: NO puede ser negativa
    if new_cantidad < 0:
        return JsonResponse({'error': 'La cantidad no puede ser menor a cero.'}, status=400)

    original_cantidad = producto.cantidad
    producto.cantidad = new_cantidad
    producto.save()

    return JsonResponse({
        'message': f'Cantidad de "{producto.nombre_producto.strip()}" actualizada de {original_cantidad} a {producto.cantidad}.',
        'cantidad_actual': producto.cantidad,
        'stock_minimo': producto.stock_minimo 
    })


def no_navio_asignado(request):

    return render(request, 'sin_navio.html', {})