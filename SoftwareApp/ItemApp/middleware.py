# ItemApp/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class UserTypeRedirectMiddleware:
    """
    Middleware que redirige automáticamente a los usuarios según su tipo:
    - Staff/Admin -> Panel de administración
    - Usuario regular -> Dashboard de usuario
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas que no necesitan redirección
        excluded_paths = [
            reverse('antepagina'),
            reverse('registro'),
            reverse('login'),
            reverse('logout'),
            '/admin/',  # Django admin
        ]
        
        # Si el usuario está autenticado y está en la ruta /inicio/
        if request.user.is_authenticated and request.path == reverse('inicio'):
            # Si es staff, redirigir al panel de admin
            if request.user.is_staff:
                return redirect('admin_panel')
        
        # Si está en admin_panel pero no es staff, redirigir a inicio
        if request.user.is_authenticated and request.path == reverse('admin_panel'):
            if not request.user.is_staff:
                return redirect('inicio')
        
        response = self.get_response(request)
        return response