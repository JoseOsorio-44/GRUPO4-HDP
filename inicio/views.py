from django.shortcuts import render, redirect
from django.http import JsonResponse
from tasks.models import Administrador, Gerente
from django.contrib import messages
from django.urls import reverse


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
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('admin_tasks:admin_view')}, status=200)
            elif user_role == 'gerente':
                return JsonResponse({'message': 'Login exitoso', 'redirect_url': reverse('gerente_tasks:gerente_view')}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)



#vista de sin permisos
def sin_permisos(request):
    return render(request, 'vista_denegada.html', {
        'message': 'No tienes los permisos necesarios para acceder a esta sección.',
        'username': request.session.get('username', 'Invitado')
    })


#cierre de sesion
def logout_view(request):
    request.session.flush()
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect(reverse('inicio:login'))
