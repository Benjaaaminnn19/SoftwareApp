#!/bin/bash
# Script de post-deploy para Railway
# Este script se ejecuta después del despliegue

# Ejecutar migraciones
cd SoftwareApp
python manage.py migrate --noinput || true

# Crear superusuario si las variables de entorno están configuradas
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python create_superuser.py || echo "No se pudo crear el superusuario (puede que ya exista)"
else
    echo "Variables de entorno para superusuario no configuradas, saltando creación"
fi
