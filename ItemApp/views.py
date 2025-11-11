# Agregar esta función al final del archivo para convertir un usuario a staff
# Esta función puede ser útil para debugging o para crear un endpoint de administración

def convertir_usuario_a_staff(request, username):
    """Función auxiliar para convertir un usuario a staff (solo para superusuarios)"""
    if not request.user.is_superuser:
        messages.error(request, 'Solo los superusuarios pueden realizar esta acción.')
        return redirect('inicio')
    
    try:
        usuario = User.objects.get(username=username)
        usuario.is_staff = True
        usuario.save()
        messages.success(request, f'Usuario {username} convertido a staff exitosamente.')
    except User.DoesNotExist:
        messages.error(request, f'Usuario {username} no encontrado.')
    
    return redirect('admin_panel')
