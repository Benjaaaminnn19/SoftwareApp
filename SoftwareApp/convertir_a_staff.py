"""
Script para convertir un usuario a staff desde la línea de comandos.
Uso: python manage.py shell < convertir_a_staff.py
O ejecuta: python manage.py shell y luego pega el código.
"""

from django.contrib.auth.models import User

# Cambia 'tu_email@ejemplo.com' por el email/username del usuario que quieres convertir a staff
username = input("Ingresa el username/email del usuario a convertir a staff: ")

try:
    usuario = User.objects.get(username=username)
    usuario.is_staff = True
    usuario.save()
    print(f"✓ Usuario {username} convertido a staff exitosamente!")
    print(f"  - Username: {usuario.username}")
    print(f"  - Email: {usuario.email}")
    print(f"  - Es staff: {usuario.is_staff}")
    print(f"  - Es superusuario: {usuario.is_superuser}")
except User.DoesNotExist:
    print(f"✗ Error: Usuario '{username}' no encontrado.")
    print("Usuarios disponibles:")
    for u in User.objects.all():
        print(f"  - {u.username} ({u.email})")








