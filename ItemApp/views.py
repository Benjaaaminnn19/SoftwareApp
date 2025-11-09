from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
import pandas as pd

from .forms import RegistroNUAMForm, ClasificacionForm, CargaMasivaForm
from .models import RegistroNUAM, Clasificacion, DatoTributario


#
# --- VISTA DE REGISTRO (NUAM) ---
#
def vista_registro(request):
    if request.method == 'POST':
        # 1. Si el formulario se envió, cárgalo con los datos
        form = RegistroNUAMForm(request.POST)
        
        if form.is_valid():
            # 2. Si los datos son válidos, sepáralos
            data = form.cleaned_data
            
            try:
                # 3. CREA EL USUARIO (para el login)
                #    Usamos el email como 'username'
                user = User.objects.create_user(
                    username=data['email'],
                    email=data['email'],
                    password=data['password']
                )
                user.first_name = data['nombre_completo']
                user.save()

                # 4. CREA EL REGISTRO (el perfil con datos extra)
                RegistroNUAM.objects.create(
                    nombre_completo=data['nombre_completo'],
                    email=data['email'],
                    pais=data['pais'],
                    identificador_tributario=data['identificador_tributario'],
                    fecha_nacimiento=data['fecha_nacimiento']
                )
                
                # 5. Redirige a la portada si todo sale bien
                messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
                return redirect('login')
            
            except Exception as e:
                # (Manejo de error básico si algo falla)
                messages.error(request, f"Ha ocurrido un error: {e}")
                form.add_error(None, f"Ha ocurrido un error inesperado: {e}")

    else:
        # 6. Si es GET (primera carga), muestra el formulario vacío
        form = RegistroNUAMForm()

    # 7. Renderiza 'login.html' (tu página de registro)
    #    y le pasa el formulario (`form`)
    return render(request, 'login.html', {'form': form}) 


# --- VISTAS EXISTENTES ---

def vista_antepagina(request):
    return render(request, 'antepagina.html')

@login_required
def vista_inicio_logueado(request):
    # Obtener estadísticas reales
    total_usuarios = User.objects.count()
    total_clasificaciones = Clasificacion.objects.count()
    total_datos = DatoTributario.objects.count()
    
    # Calcular monto total y promedio
    stats_datos = DatoTributario.objects.aggregate(
        monto_total=Sum('monto'),
        monto_promedio=Avg('monto'),
        factor_promedio=Avg('factor')
    )
    
    monto_total = stats_datos['monto_total'] or 0
    monto_promedio = stats_datos['monto_promedio'] or 0
    
    # Obtener datos recientes
    datos_recientes = DatoTributario.objects.select_related('clasificacion').order_by('-creado_en')[:10]
    
    # Estadísticas por clasificación
    stats_clasificacion = Clasificacion.objects.annotate(
        total_datos=Count('datos'),
        monto_total=Sum('datos__monto')
    ).order_by('-total_datos')[:5]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_clasificaciones': total_clasificaciones,
        'total_datos': total_datos,
        'monto_total': monto_total,
        'monto_promedio': monto_promedio,
        'datos_recientes': datos_recientes,
        'stats_clasificacion': stats_clasificacion,
    }
    
    return render(request, 'inicio.html', context)

def vista_logout(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('antepagina')

#
# --- VISTA GESTIÓN CLASIFICACIÓN ---
#
@login_required
def vista_gestion_clasificacion(request):
    # 1. Lógica para AÑADIR una nueva clasificación
    if request.method == 'POST':
        form = ClasificacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clasificación creada exitosamente.')
            return redirect('crear_clasificacion')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Si es GET, muestra un formulario vacío
        form = ClasificacionForm()

    # 2. Lógica para MOSTRAR las clasificaciones que ya existen
    clasificaciones_existentes = Clasificacion.objects.annotate(
        total_datos=Count('datos')
    ).order_by('-creado_en')

    # 3. Envía el formulario y la lista al HTML
    context = {
        'form': form,
        'clasificaciones': clasificaciones_existentes
    }
    return render(request, 'clasificacion.html', context)

@login_required
def vista_eliminar_clasificacion(request, pk):
    clasificacion = get_object_or_404(Clasificacion, pk=pk)
    if request.method == 'POST':
        nombre = clasificacion.nombre
        clasificacion.delete()
        messages.success(request, f'Clasificación "{nombre}" eliminada exitosamente.')
        return redirect('crear_clasificacion')
    context = {'clasificacion': clasificacion}
    return render(request, 'eliminar_clasificacion.html', context)

@login_required
def vista_editar_clasificacion(request, pk):
    clasificacion = get_object_or_404(Clasificacion, pk=pk)
    if request.method == 'POST':
        form = ClasificacionForm(request.POST, instance=clasificacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Clasificación actualizada exitosamente.')
            return redirect('crear_clasificacion')
    else:
        form = ClasificacionForm(instance=clasificacion)
    context = {'form': form, 'clasificacion': clasificacion}
    return render(request, 'editar_clasificacion.html', context)

#
# --- ¡VISTA NUEVA AÑADIDA! (La Carga Masiva) ---
#
@login_required
def vista_carga_datos(request):
    
    if request.method == 'POST':
        form = CargaMasivaForm(request.POST, request.FILES)
        
        if form.is_valid():
            # 1. Obtenemos los datos del formulario
            clasificacion_seleccionada = form.cleaned_data['clasificacion']
            archivo = form.cleaned_data['archivo_masivo']

            try:
                # 2. Leemos el archivo (Excel o CSV) usando pandas
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                elif archivo.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(archivo)
                else:
                    messages.error(request, 'Formato de archivo no soportado. Sube .csv o .xlsx')
                    return render(request, 'carga_datos.html', {'form': form})

                # Normalizar nombres de columnas (minúsculas, sin espacios)
                df.columns = df.columns.str.strip().str.lower()
                
                # Mapear posibles nombres de columnas
                column_mapping = {
                    'monto': ['monto', 'amount', 'valor', 'value'],
                    'factor': ['factor', 'factor_', 'multiplicador'],
                    'nombre': ['nombre', 'name', 'nombre_dato', 'descripcion', 'descripción'],
                    'fecha': ['fecha', 'date', 'fecha_dato', 'fecha_dato']
                }
                
                # Encontrar las columnas correctas
                monto_col = None
                factor_col = None
                nombre_col = None
                fecha_col = None
                
                for col in df.columns:
                    col_lower = col.lower()
                    if not monto_col and any(x in col_lower for x in column_mapping['monto']):
                        monto_col = col
                    if not factor_col and any(x in col_lower for x in column_mapping['factor']):
                        factor_col = col
                    if not nombre_col and any(x in col_lower for x in column_mapping['nombre']):
                        nombre_col = col
                    if not fecha_col and any(x in col_lower for x in column_mapping['fecha']):
                        fecha_col = col
                
                if not nombre_col:
                    messages.error(request, 'No se encontró una columna de nombre en el archivo.')
                    return render(request, 'carga_datos.html', {'form': form})
                
                # 3. Iteramos sobre cada fila del archivo
                registros_creados = 0
                errores = []
                
                for index, fila in df.iterrows():
                    try:
                        # 4. Creamos el objeto en la base de datos
                        nombre_dato = str(fila[nombre_col]) if nombre_col else f'Dato {index + 1}'
                        monto = pd.to_numeric(fila[monto_col], errors='coerce') if monto_col else None
                        factor = pd.to_numeric(fila[factor_col], errors='coerce') if factor_col else None
                        fecha_dato_val = None
                        if fecha_col:
                            try:
                                fecha_parseada = pd.to_datetime(fila[fecha_col], errors='coerce')
                                if pd.notna(fecha_parseada):
                                    fecha_dato_val = fecha_parseada.date()
                            except:
                                fecha_dato_val = None
                        
                        DatoTributario.objects.create(
                            clasificacion=clasificacion_seleccionada,
                            monto=float(monto) if monto is not None and pd.notna(monto) else None,
                            factor=float(factor) if factor is not None and pd.notna(factor) else None,
                            nombre_dato=nombre_dato.strip() if nombre_dato else f'Dato {index + 1}',
                            fecha_dato=fecha_dato_val
                        )
                        registros_creados += 1
                    except Exception as e:
                        errores.append(f"Fila {index + 2}: {str(e)}")
                
                # 5. Si todo sale bien, redirige de vuelta
                if registros_creados > 0:
                    messages.success(request, f'Se cargaron exitosamente {registros_creados} registros.')
                if errores:
                    messages.warning(request, f'Se encontraron {len(errores)} errores al procesar algunas filas.')
                return redirect('carga_datos') 

            except Exception as e:
                # Si hay un error leyendo el archivo (ej: columnas incorrectas)
                messages.error(request, f"Error al procesar el archivo: {e}")
                form.add_error(None, f"Error al procesar el archivo: {e}")

    else:
        form = CargaMasivaForm()

    context = {
        'form': form,
    }
    return render(request, 'carga_datos.html', context)

@login_required
def vista_listar_datos_tributarios(request):
    # Obtener parámetros de búsqueda y filtro
    busqueda = request.GET.get('q', '')
    clasificacion_id = request.GET.get('clasificacion', '')
    
    # Consulta base
    datos = DatoTributario.objects.select_related('clasificacion').all()
    
    # Aplicar filtros
    if busqueda:
        datos = datos.filter(
            Q(nombre_dato__icontains=busqueda) |
            Q(clasificacion__nombre__icontains=busqueda)
        )
    
    if clasificacion_id:
        datos = datos.filter(clasificacion_id=clasificacion_id)
    
    # Ordenar
    datos = datos.order_by('-creado_en')
    
    # Paginación
    paginator = Paginator(datos, 20)  # 20 elementos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener todas las clasificaciones para el filtro
    clasificaciones = Clasificacion.objects.all()
    
    context = {
        'page_obj': page_obj,
        'clasificaciones': clasificaciones,
        'busqueda': busqueda,
        'clasificacion_seleccionada': clasificacion_id,
    }
    
    return render(request, 'listar_datos_tributarios.html', context)

@login_required
def vista_eliminar_dato_tributario(request, pk):
    dato = get_object_or_404(DatoTributario, pk=pk)
    if request.method == 'POST':
        nombre = dato.nombre_dato
        dato.delete()
        messages.success(request, f'Dato "{nombre}" eliminado exitosamente.')
        return redirect('listar_datos_tributarios')
    context = {'dato': dato}
    return render(request, 'eliminar_dato_tributario.html', context)