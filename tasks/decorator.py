# tasks/decorators.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles=None):
    """
    Decorador que verifica si el usuario en la sesión tiene uno de los roles permitidos.
    Redirige a la página de login si no está autenticado.
    Redirige a 'no_permission.html' si no tiene el rol correcto.
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_role = request.session.get('user_role')

            if not user_role:
                messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect(reverse('login'))
            elif user_role not in allowed_roles:
                messages.warning(request, 'Acceso denegado.') 
                return redirect(reverse('no_permission')) 

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator