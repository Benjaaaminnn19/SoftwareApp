from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, Avg, Max, Min
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import io
from decimal import Decimal
from dateutil import parser

from .forms import RegistroNUAMForm, ClasificacionForm, CargaMasivaForm, CalificacionTributariaForm, ModificarCalificacionTributariaForm
from .models import RegistroNUAM, Clasificacion, DatoTributario, CalificacionTributaria, PerfilUsuario


# ============================================================================
# FUNCIONES DE VERIFICACIÓN DE PERMISOS
# ============================================================================

def es_staff(user):
    """Verifica si el usuario es staff (administrador)"""
    return user.is_staff

def es_usuario_regular(user):
    """Verifica si el usuario es regular (no staff)"""
    return not user.is_staff

def tiene_rol(user, rol):
    """Verifica si el usuario tiene un rol específico"""
    if not user.is_authenticated:
        return False
    try:
        perfil = user.perfil
        return perfil.rol == rol
    except PerfilUsuario.DoesNotExist:
        # Si no tiene perfil, verificar si es staff (admin)
        if rol == 'admin':
            return user.is_staff
        return False

def es_admin(user):
    """Verifica si el usuario es administrador"""
    return tiene_rol(user, 'admin') or user.is_staff

def es_corredor(user):
    """Verifica si el usuario es corredor"""
    return tiene_rol(user, 'corredor')

def es_tributario(user):
    """Verifica si el usuario es tributario"""
    return tiene_rol(user, 'tributario')

def puede_gestionar_calificaciones(user):
    """Verifica si el usuario puede gestionar calificaciones (admin, corredor o tributario)"""
    return es_admin(user) or es_corredor(user) or es_tributario(user)


# Vista personalizada de login que redirige según el tipo de usuario
class CustomLoginView(LoginView):
    template_name = 'login_tradicional.html'
    
    def get_success_url(self):
        """Redirige según el tipo de usuario después del login"""
        # Si hay un parámetro 'next', usarlo
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        
        # Si el usuario es staff, redirigir al panel de admin
        if self.request.user.is_staff:
            return '/admin-panel/'
        
        # Si no, redirigir al dashboard normal
        return '/inicio/'


# ============================================================================
# VISTAS PÚBLICAS (Sin autenticación)
# ============================================================================

def vista_antepagina(request):
    """Página de inicio/landing"""
    return render(request, 'antepagina.html')


def vista_registro(request):
    """Registro de nuevos usuarios"""
    if request.method == 'POST':
        form = RegistroNUAMForm(request.POST)
        
        if form.is_valid():
            data = form.cleaned_data
            
            try:
                # Crear usuario
                user = User.objects.create_user(
                    username=data['email'],
                    email=data['email'],
                    password=data['password']
                )
                user.first_name = data['nombre_completo']
                user.save()

                # Crear registro NUAM
                RegistroNUAM.objects.create(
                    nombre_completo=data['nombre_completo'],
                    email=data['email'],
                    pais=data['pais'],
                    identificador_tributario=data['identificador_tributario'],
                    fecha_nacimiento=data['fecha_nacimiento']
                )
                
                messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión.')
                return redirect('login')
            
            except Exception as e:
                messages.error(request, f'Ha ocurrido un error: {e}')
    else:
        form = RegistroNUAMForm()

    return render(request, 'login.html', {'form': form})


def vista_logout(request):
    """Cerrar sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('antepagina')


# ============================================================================
# VISTAS PARA USUARIOS REGULARES (Requiere login, NO staff)
# ============================================================================

@login_required
@user_passes_test(es_usuario_regular, login_url='admin_panel')
def vista_inicio_usuario(request):
    """Dashboard simplificado para usuarios regulares"""
    
    # Estadísticas básicas
    total_clasificaciones = Clasificacion.objects.count()
    total_datos = DatoTributario.objects.count()
    total_calificaciones = CalificacionTributaria.objects.count()
    
    # Monto total
    monto_total = DatoTributario.objects.aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0')
    
    # Datos recientes (últimos 5)
    datos_recientes = DatoTributario.objects.select_related(
        'clasificacion'
    ).order_by('-creado_en')[:5]
    
    # Estadísticas por clasificación
    stats_clasificacion = Clasificacion.objects.annotate(
        total_datos=Count('datos'),
        monto_total=Sum('datos__monto')
    ).filter(total_datos__gt=0).order_by('-monto_total')
    
    context = {
        'total_clasificaciones': total_clasificaciones,
        'total_datos': total_datos,
        'total_calificaciones': total_calificaciones,
        'monto_total': monto_total,
        'datos_recientes': datos_recientes,
        'stats_clasificacion': stats_clasificacion,
    }
    
    return render(request, 'inicio_usuario.html', context)


# ============================================================================
# VISTAS PARA ADMINISTRADORES (Requiere staff)
# ============================================================================

@login_required
def vista_panel_administracion(request):
    """Panel de administración completo - SOLO PARA STAFF"""
    
    # Verificar que el usuario sea staff
    if not request.user.is_staff:
        messages.warning(
            request, 
            f'⚠️ Acceso denegado: Tu usuario ({request.user.username}) no tiene permisos de administrador. '
            f'Necesitas tener permisos de "Staff" para acceder al panel de administración. '
            f'Por favor, contacta al administrador del sistema o accede al Django Admin para activar los permisos.'
        )
        return redirect('inicio')
    
    # Estadísticas de usuarios
    total_usuarios = User.objects.count()
    total_staff = User.objects.filter(is_staff=True).count()
    total_superusuarios = User.objects.filter(is_superuser=True).count()
    total_usuarios_regulares = total_usuarios - total_staff
    
    # Estadísticas financieras
    stats_financieras = DatoTributario.objects.aggregate(
        monto_total=Sum('monto'),
        monto_promedio=Avg('monto'),
        monto_maximo=Max('monto'),
        monto_minimo=Min('monto'),
        factor_promedio=Avg('factor')
    )
    
    # Estadísticas de clasificaciones y datos
    total_clasificaciones = Clasificacion.objects.count()
    total_datos_tributarios = DatoTributario.objects.count()
    total_registros_nuam = RegistroNUAM.objects.count()
    
    # Actividad últimos 30 días
    hace_30_dias = timezone.now() - timedelta(days=30)
    
    usuarios_nuevos_30d = User.objects.filter(
        date_joined__gte=hace_30_dias
    ).count()
    
    usuarios_activos_30d = User.objects.filter(
        last_login__gte=hace_30_dias
    ).count()
    
    datos_nuevos_30d = DatoTributario.objects.filter(
        creado_en__gte=hace_30_dias
    ).count()
    
    registros_nuevos_30d = RegistroNUAM.objects.filter(
        creado_en__gte=hace_30_dias
    ).count()
    
    # Usuarios recientes
    usuarios_recientes = User.objects.order_by('-date_joined')[:10]
    
    # Registros NUAM recientes
    registros_recientes = RegistroNUAM.objects.order_by('-creado_en')[:10]
    
    # Datos tributarios recientes
    datos_recientes = DatoTributario.objects.select_related(
        'clasificacion'
    ).order_by('-creado_en')[:10]
    
    # Estadísticas por país
    stats_paises = RegistroNUAM.objects.values('pais').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Estadísticas por clasificación
    stats_clasificacion = Clasificacion.objects.annotate(
        total_datos=Count('datos'),
        monto_total=Sum('datos__monto')
    ).filter(total_datos__gt=0).order_by('-monto_total')
    
    context = {
        # Estadísticas principales
        'total_usuarios': total_usuarios,
        'total_staff': total_staff,
        'total_superusuarios': total_superusuarios,
        'total_usuarios_regulares': total_usuarios_regulares,
        'total_clasificaciones': total_clasificaciones,
        'total_datos_tributarios': total_datos_tributarios,
        'total_registros_nuam': total_registros_nuam,
        
        # Estadísticas financieras
        'monto_total': stats_financieras['monto_total'] or Decimal('0'),
        'monto_promedio': stats_financieras['monto_promedio'] or Decimal('0'),
        'monto_maximo': stats_financieras['monto_maximo'] or Decimal('0'),
        'monto_minimo': stats_financieras['monto_minimo'] or Decimal('0'),
        'factor_promedio': stats_financieras['factor_promedio'] or Decimal('0'),
        
        # Actividad
        'usuarios_nuevos_30d': usuarios_nuevos_30d,
        'usuarios_activos_30d': usuarios_activos_30d,
        'datos_nuevos_30d': datos_nuevos_30d,
        'registros_nuevos_30d': registros_nuevos_30d,
        
        # Listas
        'usuarios_recientes': usuarios_recientes,
        'registros_recientes': registros_recientes,
        'datos_recientes': datos_recientes,
        'stats_paises': stats_paises,
        'stats_clasificacion': stats_clasificacion,
    }
    
    return render(request, 'admin_panel.html', context)


# ============================================================================
# VISTAS COMPARTIDAS (Tanto usuarios como admins)
# ============================================================================

@login_required
@user_passes_test(es_staff, login_url='inicio')
def vista_gestion_clasificacion(request):
    """Gestión de clasificaciones - SOLO ADMIN"""
    if not request.user.is_staff:
        messages.warning(request, '⚠️ Solo los administradores pueden gestionar clasificaciones.')
        return redirect('inicio')
    if request.method == 'POST':
        form = ClasificacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clasificación creada exitosamente.')
            return redirect('crear_clasificacion')
    else:
        form = ClasificacionForm()

    clasificaciones_existentes = Clasificacion.objects.annotate(
        total_datos=Count('datos')
    ).order_by('-creado_en')

    context = {
        'form': form,
        'clasificaciones': clasificaciones_existentes
    }
    return render(request, 'clasificacion.html', context)


@login_required
@user_passes_test(es_staff, login_url='inicio')
def vista_editar_clasificacion(request, pk):
    """Editar clasificación existente - SOLO ADMIN"""
    if not request.user.is_staff:
        messages.warning(request, '⚠️ Solo los administradores pueden editar clasificaciones.')
        return redirect('crear_clasificacion')
    
    clasificacion = get_object_or_404(Clasificacion, pk=pk)
    
    if request.method == 'POST':
        form = ClasificacionForm(request.POST, instance=clasificacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clasificación actualizada exitosamente.')
            return redirect('crear_clasificacion')
    else:
        form = ClasificacionForm(instance=clasificacion)
    
    context = {
        'form': form,
        'clasificacion': clasificacion
    }
    return render(request, 'editar_clasificacion.html', context)


@login_required
@user_passes_test(es_staff, login_url='inicio')
def vista_eliminar_clasificacion(request, pk):
    """Eliminar clasificación - SOLO ADMIN"""
    if not request.user.is_staff:
        messages.warning(request, '⚠️ Solo los administradores pueden eliminar clasificaciones.')
        return redirect('crear_clasificacion')
    
    clasificacion = get_object_or_404(Clasificacion, pk=pk)
    
    if request.method == 'POST':
        nombre = clasificacion.nombre
        clasificacion.delete()
        messages.success(request, f'Clasificación "{nombre}" eliminada exitosamente.')
        return redirect('crear_clasificacion')
    
    context = {
        'clasificacion': clasificacion
    }
    return render(request, 'eliminar_clasificacion.html', context)


@login_required
@user_passes_test(es_staff, login_url='inicio')
def vista_carga_datos(request):
    """Carga masiva de datos - SOLO ADMIN"""
    if not request.user.is_staff:
        messages.warning(request, '⚠️ Solo los administradores pueden cargar datos.')
        return redirect('inicio')
    if request.method == 'POST':
        form = CargaMasivaForm(request.POST, request.FILES)
        
        if form.is_valid():
            clasificacion_seleccionada = form.cleaned_data['clasificacion']
            archivo = form.cleaned_data['archivo_masivo']
            modo_carga = form.cleaned_data['modo_carga']

            try:
                # Leer archivo
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                elif archivo.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(archivo)
                else:
                    messages.error(request, 'Formato de archivo no soportado.')
                    return redirect('carga_datos')

                # Detectar columnas
                columnas_nombre = ['nombre', 'name', 'nombre_dato', 'descripcion', 'desc', 'dato', 'item']
                columnas_monto = ['monto', 'amount', 'valor', 'value', 'precio', 'price', 'importe']
                columnas_factor = ['factor', 'factor_', 'multiplicador', 'multiplier', 'ratio', 'coeficiente']
                columnas_fecha = ['fecha', 'date', 'fecha_dato', 'fecha_creacion', 'created_at']

                col_nombre = None
                col_monto = None
                col_factor = None
                col_fecha = None

                for col in df.columns:
                    col_lower = col.lower().strip()
                    if col_lower in columnas_nombre and col_nombre is None:
                        col_nombre = col
                    elif col_lower in columnas_monto and col_monto is None:
                        col_monto = col
                    elif col_lower in columnas_factor and col_factor is None:
                        col_factor = col
                    elif col_lower in columnas_fecha and col_fecha is None:
                        col_fecha = col

                if col_nombre is None:
                    messages.error(request, 'No se encontró columna de nombre.')
                    return redirect('carga_datos')

                # Procesar datos
                registros_creados = 0
                registros_actualizados = 0

                for index, fila in df.iterrows():
                    nombre_valor = str(fila.get(col_nombre, '')).strip()
                    if not nombre_valor or nombre_valor == 'nan':
                        continue

                    datos = {
                        'clasificacion': clasificacion_seleccionada,
                        'nombre_dato': nombre_valor
                    }

                    if col_monto and pd.notna(fila.get(col_monto)):
                        try:
                            datos['monto'] = Decimal(str(fila[col_monto]))
                        except:
                            pass

                    if col_factor and pd.notna(fila.get(col_factor)):
                        try:
                            datos['factor'] = Decimal(str(fila[col_factor]))
                        except:
                            pass

                    if col_fecha and pd.notna(fila.get(col_fecha)):
                        try:
                            fecha_parsed = parser.parse(str(fila[col_fecha]))
                            datos['fecha_dato'] = fecha_parsed.date()
                        except:
                            pass

                    if modo_carga == 'actualizar':
                        obj, created = DatoTributario.objects.update_or_create(
                            nombre_dato=nombre_valor,
                            clasificacion=clasificacion_seleccionada,
                            defaults=datos
                        )
                        if created:
                            registros_creados += 1
                        else:
                            registros_actualizados += 1
                    else:
                        DatoTributario.objects.create(**datos)
                        registros_creados += 1

                mensaje = f'Carga exitosa: {registros_creados} registros creados'
                if registros_actualizados > 0:
                    mensaje += f', {registros_actualizados} actualizados'
                messages.success(request, mensaje)
                return redirect('carga_datos')

            except Exception as e:
                messages.error(request, f'Error al procesar: {e}')

    else:
        form = CargaMasivaForm()

    # Estadísticas
    total_datos = DatoTributario.objects.count()
    ultimas_cargas = DatoTributario.objects.select_related(
        'clasificacion'
    ).order_by('-creado_en')[:10]

    context = {
        'form': form,
        'total_datos': total_datos,
        'ultimas_cargas': ultimas_cargas,
    }
    return render(request, 'carga_datos.html', context)


@login_required
def vista_listar_datos_tributarios(request):
    """Listar y filtrar datos tributarios"""
    datos = DatoTributario.objects.select_related('clasificacion').order_by('-creado_en')
    
    # Filtros
    busqueda = request.GET.get('q', '')
    clasificacion_id = request.GET.get('clasificacion', '')
    
    if busqueda:
        datos = datos.filter(nombre_dato__icontains=busqueda)
    
    if clasificacion_id:
        datos = datos.filter(clasificacion_id=clasificacion_id)
    
    # Paginación
    paginator = Paginator(datos, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    clasificaciones = Clasificacion.objects.all().order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'clasificaciones': clasificaciones,
        'busqueda': busqueda,
        'clasificacion_seleccionada': clasificacion_id,
    }
    return render(request, 'listar_datos_tributarios.html', context)


@login_required
@user_passes_test(es_staff, login_url='inicio')
def vista_eliminar_dato_tributario(request, pk):
    """Eliminar dato tributario - SOLO ADMIN"""
    if not request.user.is_staff:
        messages.warning(request, '⚠️ Solo los administradores pueden eliminar datos tributarios.')
        return redirect('listar_datos_tributarios')
    
    dato = get_object_or_404(DatoTributario, pk=pk)
    
    if request.method == 'POST':
        nombre = dato.nombre_dato
        dato.delete()
        messages.success(request, f'Dato "{nombre}" eliminado exitosamente.')
        return redirect('listar_datos_tributarios')
    
    context = {
        'dato': dato
    }
    return render(request, 'eliminar_dato_tributario.html', context)


@login_required
def descargar_plantilla_excel(request):
    """Descargar plantilla Excel de ejemplo"""
    datos_ejemplo = {
        'Nombre': ['Ejemplo Dato 1', 'Ejemplo Dato 2', 'Ejemplo Dato 3'],
        'Monto': [1000000.50, 2500000.00, 500000.75],
        'Factor': [1.05, 1.15, 1.02],
        'Fecha': ['2024-01-15', '2024-02-20', '2024-03-10']
    }
    
    df = pd.DataFrame(datos_ejemplo)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=plantilla_carga_datos.xlsx'
    
    return response


@login_required
def vista_preview_archivo(request):
    """Vista previa del archivo antes de cargar"""
    # Implementación futura si se requiere
    pass


@login_required
def vista_reportes(request):
    """Página de reportes y estadísticas"""
    
    # Estadísticas generales
    total_datos = DatoTributario.objects.count()
    total_clasificaciones = Clasificacion.objects.count()
    
    # Estadísticas financieras
    stats_financieras = DatoTributario.objects.aggregate(
        monto_total=Sum('monto'),
        monto_promedio=Avg('monto'),
        monto_maximo=Max('monto'),
        monto_minimo=Min('monto'),
        factor_promedio=Avg('factor'),
        total_con_monto=Count('id', filter=Q(monto__isnull=False))
    )
    
    # Estadísticas por clasificación
    stats_por_clasificacion = Clasificacion.objects.annotate(
        total_datos=Count('datos'),
        monto_total=Sum('datos__monto'),
        monto_promedio=Avg('datos__monto')
    ).filter(total_datos__gt=0).order_by('-monto_total')
    
    # Datos recientes (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    datos_recientes_30d = DatoTributario.objects.filter(
        creado_en__gte=hace_30_dias
    ).count()
    
    # Top 10 datos por monto
    top_datos_monto = DatoTributario.objects.filter(
        monto__isnull=False
    ).select_related('clasificacion').order_by('-monto')[:10]
    
    # Estadísticas por mes (últimos 6 meses)
    from django.db.models.functions import TruncMonth
    stats_por_mes = DatoTributario.objects.annotate(
        mes=TruncMonth('creado_en')
    ).values('mes').annotate(
        total=Count('id'),
        monto_total=Sum('monto')
    ).order_by('-mes')[:6]
    
    # Clasificaciones más usadas
    clasificaciones_mas_usadas = Clasificacion.objects.annotate(
        total_datos=Count('datos')
    ).filter(total_datos__gt=0).order_by('-total_datos')[:5]
    
    context = {
        # Estadísticas generales
        'total_datos': total_datos,
        'total_clasificaciones': total_clasificaciones,
        'datos_recientes_30d': datos_recientes_30d,
        
        # Estadísticas financieras
        'monto_total': stats_financieras['monto_total'] or Decimal('0'),
        'monto_promedio': stats_financieras['monto_promedio'] or Decimal('0'),
        'monto_maximo': stats_financieras['monto_maximo'] or Decimal('0'),
        'monto_minimo': stats_financieras['monto_minimo'] or Decimal('0'),
        'factor_promedio': stats_financieras['factor_promedio'] or Decimal('0'),
        'total_con_monto': stats_financieras['total_con_monto'] or 0,
        
        # Estadísticas detalladas
        'stats_por_clasificacion': stats_por_clasificacion,
        'top_datos_monto': top_datos_monto,
        'stats_por_mes': stats_por_mes,
        'clasificaciones_mas_usadas': clasificaciones_mas_usadas,
    }
    
    return render(request, 'reportes.html', context)


# ============================================================================
# VISTAS PARA CALIFICACIONES TRIBUTARIAS
# ============================================================================

@login_required
def vista_listar_calificaciones(request):
    """Listar calificaciones tributarias con filtros"""
    calificaciones = CalificacionTributaria.objects.all().order_by('-año', '-fecha_pago', 'instrumento')
    
    # Filtros
    mercado = request.GET.get('mercado', '')
    origen = request.GET.get('origen', '')
    calificacion_pendiente = request.GET.get('calificacion_pendiente', '')
    periodo_comercial = request.GET.get('periodo_comercial', '')
    busqueda = request.GET.get('q', '')
    
    if mercado:
        calificaciones = calificaciones.filter(mercado=mercado)
    
    if origen:
        calificaciones = calificaciones.filter(origen=origen)
    
    if calificacion_pendiente == 'true':
        calificaciones = calificaciones.filter(calificacion_pendiente=True)
    elif calificacion_pendiente == 'false':
        calificaciones = calificaciones.filter(calificacion_pendiente=False)
    
    if periodo_comercial:
        try:
            año = int(periodo_comercial)
            calificaciones = calificaciones.filter(año=año)
        except ValueError:
            pass
    
    if busqueda:
        calificaciones = calificaciones.filter(
            Q(instrumento__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(secuencia_evento__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(calificaciones, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'mercado_seleccionado': mercado,
        'origen_seleccionado': origen,
        'calificacion_pendiente_filtro': calificacion_pendiente,
        'periodo_comercial_filtro': periodo_comercial,
        'busqueda': busqueda,
        'mercados': CalificacionTributaria.MERCADO_CHOICES,
        'origenes': CalificacionTributaria.ORIGEN_CHOICES,
    }
    
    return render(request, 'calificaciones/listar_calificaciones.html', context)


@login_required
@user_passes_test(puede_gestionar_calificaciones, login_url='inicio')
def vista_ingresar_calificacion(request):
    """Vista para ingresar una nueva calificación tributaria"""
    if request.method == 'POST':
        form = CalificacionTributariaForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.creado_por = request.user
            # Asignar origen según el rol del usuario
            try:
                perfil = request.user.perfil
                if perfil.rol == 'corredor':
                    calificacion.origen = 'CORREDOR'
                elif perfil.rol == 'tributario':
                    calificacion.origen = 'TRIBUTARIO'
                else:
                    calificacion.origen = 'ADMIN'
            except PerfilUsuario.DoesNotExist:
                calificacion.origen = 'ADMIN' if request.user.is_staff else 'CORREDOR'
            
            calificacion.save()
            messages.success(request, 'Calificación ingresada exitosamente.')
            return redirect('listar_calificaciones')
    else:
        form = CalificacionTributariaForm()
        # Establecer valores por defecto
        form.fields['año'].initial = timezone.now().year
        form.fields['secuencia_evento'].initial = '100000807'
    
    context = {
        'form': form,
    }
    return render(request, 'calificaciones/ingresar_calificacion.html', context)


@login_required
@user_passes_test(puede_gestionar_calificaciones, login_url='inicio')
def vista_modificar_calificacion(request, pk):
    """Vista para modificar una calificación tributaria existente"""
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    
    if request.method == 'POST':
        form = ModificarCalificacionTributariaForm(request.POST, instance=calificacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calificación modificada exitosamente.')
            return redirect('listar_calificaciones')
    else:
        form = ModificarCalificacionTributariaForm(instance=calificacion)
    
    # Importar descripciones de factores desde forms
    from .forms import FACTOR_DESCRIPTIONS
    
    context = {
        'form': form,
        'calificacion': calificacion,
        'factor_descriptions': FACTOR_DESCRIPTIONS,
    }
    return render(request, 'calificaciones/modificar_calificacion.html', context)


@login_required
@user_passes_test(es_admin, login_url='inicio')
def vista_eliminar_calificacion(request, pk):
    """Vista para eliminar una calificación tributaria - SOLO ADMIN"""
    calificacion = get_object_or_404(CalificacionTributaria, pk=pk)
    
    if request.method == 'POST':
        instrumento = calificacion.instrumento
        calificacion.delete()
        messages.success(request, f'Calificación "{instrumento}" eliminada exitosamente.')
        return redirect('listar_calificaciones')
    
    context = {
        'calificacion': calificacion
    }
    return render(request, 'calificaciones/eliminar_calificacion.html', context)


@login_required
@user_passes_test(puede_gestionar_calificaciones, login_url='inicio')
def vista_copiar_calificacion(request, pk):
    """Vista para copiar una calificación tributaria"""
    calificacion_original = get_object_or_404(CalificacionTributaria, pk=pk)
    
    if request.method == 'POST':
        # Generar secuencia única para la copia
        import time
        nueva_secuencia = f"{calificacion_original.secuencia_evento}_COPIA_{int(time.time())}"
        
        # Crear una copia usando todos los campos
        nueva_calificacion = CalificacionTributaria()
        nueva_calificacion.mercado = calificacion_original.mercado
        nueva_calificacion.instrumento = calificacion_original.instrumento
        nueva_calificacion.descripcion = calificacion_original.descripcion
        nueva_calificacion.fecha_pago = calificacion_original.fecha_pago
        nueva_calificacion.secuencia_evento = nueva_secuencia
        nueva_calificacion.dividendo = calificacion_original.dividendo
        nueva_calificacion.valor_historico = calificacion_original.valor_historico
        nueva_calificacion.factor_actualizacion = calificacion_original.factor_actualizacion
        nueva_calificacion.año = calificacion_original.año
        nueva_calificacion.isfut = calificacion_original.isfut
        nueva_calificacion.origen = calificacion_original.origen
        nueva_calificacion.calificacion_pendiente = calificacion_original.calificacion_pendiente
        nueva_calificacion.periodo_comercial = calificacion_original.periodo_comercial
        nueva_calificacion.evento_capital = calificacion_original.evento_capital
        
        # Copiar todos los factores
        for i in range(8, 38):
            setattr(nueva_calificacion, f'factor_{i:02d}', getattr(calificacion_original, f'factor_{i:02d}'))
        nueva_calificacion.factor_198 = calificacion_original.factor_198
        
        nueva_calificacion.creado_por = request.user
        nueva_calificacion.save()
        
        messages.success(request, 'Calificación copiada exitosamente.')
        return redirect('modificar_calificacion', pk=nueva_calificacion.pk)
    
    context = {
        'calificacion': calificacion_original
    }
    return render(request, 'calificaciones/copiar_calificacion.html', context)