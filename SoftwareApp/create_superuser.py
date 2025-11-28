#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SoftwareApp.settings')
django.setup()

from django.contrib.auth.models import User

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superusuario '{username}' creado exitosamente")
    else:
        print(f"Superusuario '{username}' ya existe")
else:
    print("Variables de entorno DJANGO_SUPERUSER_USERNAME o DJANGO_SUPERUSER_PASSWORD no están configuradas")
