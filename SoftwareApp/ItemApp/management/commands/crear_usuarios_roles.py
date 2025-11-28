"""
Comando de gestión para crear usuarios con roles específicos.

Uso:
    python manage.py crear_usuarios_roles
    python manage.py crear_usuarios_roles --username admin2 --email admin2@example.com --password admin123 --rol admin
    python manage.py crear_usuarios_roles --rol tributario
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from ItemApp.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Crea usuarios con roles específicos (admin, tributario, corredor)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email del usuario'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña del usuario'
        )
        parser.add_argument(
            '--rol',
            type=str,
            choices=['admin', 'tributario', 'corredor'],
            default='corredor',
            help='Rol del usuario (admin, tributario, corredor)'
        )
        parser.add_argument(
            '--crear-predefinidos',
            action='store_true',
            help='Crear 3 usuarios predefinidos: admin, tributario, corredor'
        )

    def handle(self, *args, **options):
        if options['crear_predefinidos']:
            self._crear_usuarios_predefinidos()
        elif options['username']:
            self._crear_usuario_individual(options)
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Uso: python manage.py crear_usuarios_roles --username <user> --email <email> --password <pass> --rol <rol>\n'
                    'O: python manage.py crear_usuarios_roles --crear-predefinidos'
                )
            )

    def _crear_usuarios_predefinidos(self):
        """Crear 3 usuarios predefinidos con sus roles"""
        usuarios_predefinidos = [
            {
                'username': 'admin_user',
                'email': 'admin@example.com',
                'password': 'AdminPass123!',
                'rol': 'admin',
                'is_staff': True,
                'is_superuser': False,
            },
            {
                'username': 'tributario_user',
                'email': 'tributario@example.com',
                'password': 'TributarioPass123!',
                'rol': 'tributario',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'corredor_user',
                'email': 'corredor@example.com',
                'password': 'CorredorPass123!',
                'rol': 'corredor',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        for usuario_data in usuarios_predefinidos:
            self._crear_usuario_individual(usuario_data)

    def _crear_usuario_individual(self, options):
        """Crear un usuario individual"""
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        rol = options.get('rol', 'corredor')
        is_staff = options.get('is_staff', rol == 'admin')
        is_superuser = options.get('is_superuser', False)

        if not username or not email or not password:
            raise CommandError('Debes proporcionar username, email y password')

        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'El usuario "{username}" ya existe.')
                )
                return

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=is_staff,
                is_superuser=is_superuser,
                first_name=username.capitalize()
            )

            perfil, created = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={'rol': rol}
            )

            if not created:
                perfil.rol = rol
                perfil.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Usuario "{username}" creado exitosamente con rol "{rol}"'
                )
            )
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Password: {password}')

        except Exception as e:
            raise CommandError(f'Error al crear usuario: {str(e)}')
