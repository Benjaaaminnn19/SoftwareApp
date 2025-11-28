
cd SoftwareApp
python manage.py migrate --noinput || true


if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python create_superuser.py || echo "No se pudo crear el superusuario (puede que ya exista)"
else
    echo "Variables de entorno para superusuario no configuradas, saltando creación"
fi
