from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import pandas as pd
import io
import json
from datetime import datetime

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
# --- FUNCIONES AUXILIARES PARA CARGA DE DATOS ---
#

def leer_archivo_excel(archivo):
    """Lee un archivo Excel o CSV y retorna un DataFrame"""
    nombre = archivo.name.lower()
    try:
        if nombre.endswith('.csv'):
            # Intentar diferentes encodings
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    archivo.seek(0)  # Reiniciar el archivo
                    df = pd.read_csv(archivo, encoding=encoding)
                    return df
                except UnicodeDecodeError:
                    continue
            # Si ninguno funciona, usar el último
            archivo.seek(0)
            return pd.read_csv(archivo, encoding='utf-8', errors='ignore')
        elif nombre.endswith(('.xls', '.xlsx')):
            archivo.seek(0)
            return pd.read_excel(archivo, engine='openpyxl' if nombre.endswith('.xlsx') else None)
        else:
            raise ValueError("Formato de archivo no soportado")
    except Exception as e:
        raise ValueError(f"Error al leer el archivo: {str(e)}")


def detectar_columnas(df):
    """Detecta automáticamente las columnas del archivo"""
    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip()
    columnas_originales = df.columns.tolist()
    df.columns = df.columns.str.lower().str.strip()
    
    # Mapeo de posibles nombres
    mapeo_columnas = {
        'nombre': ['nombre', 'name', 'nombre_dato', 'descripcion', 'descripción', 'desc', 'dato', 'item'],
        'monto': ['monto', 'amount', 'valor', 'value', 'precio', 'price', 'importe'],
        'factor': ['factor', 'factor_', 'multiplicador', 'multiplier', 'ratio', 'coeficiente'],
        'fecha': ['fecha', 'date', 'fecha_dato', 'fecha_dato', 'fecha_creacion', 'created_at']
    }
    
    columnas_detectadas = {}
    columnas_no_detectadas = []
    
    for tipo, posibles_nombres in mapeo_columnas.items():
        encontrada = None
        for col in df.columns:
            col_clean = col.lower().strip()
            if any(nombre in col_clean for nombre in posibles_nombres):
                encontrada = col
                break
        
        if encontrada:
            # Buscar el nombre original
            idx = df.columns.get_loc(encontrada)
            columnas_detectadas[tipo] = {
                'nombre_original': columnas_originales[idx],
                'nombre_normalizado': encontrada,
                'indice': idx
            }
        else:
            if tipo == 'nombre':  # Nombre es obligatorio
                columnas_no_detectadas.append(tipo)
    
    return columnas_detectadas, columnas_no_detectadas, columnas_originales


def validar_fila_datos(fila, columnas_detectadas, index):
    """Valida una fila de datos y retorna los datos procesados y errores"""
    errores = []
    datos = {}
    
    # Procesar nombre (obligatorio)
    if 'nombre' in columnas_detectadas:
        nombre_col = columnas_detectadas['nombre']['nombre_normalizado']
        nombre = str(fila.get(nombre_col, '')).strip()
        if not nombre or nombre == 'nan' or nombre == '':
            errores.append(f"Fila {index + 2}: El nombre está vacío")
        else:
            datos['nombre_dato'] = nombre
    else:
        errores.append(f"Fila {index + 2}: No se encontró columna de nombre")
    
    # Procesar monto (opcional)
    if 'monto' in columnas_detectadas:
        monto_col = columnas_detectadas['monto']['nombre_normalizado']
        try:
            monto_val = pd.to_numeric(fila.get(monto_col), errors='coerce')
            if pd.notna(monto_val):
                datos['monto'] = float(monto_val)
            else:
                datos['monto'] = None
        except:
            datos['monto'] = None
    
    # Procesar factor (opcional)
    if 'factor' in columnas_detectadas:
        factor_col = columnas_detectadas['factor']['nombre_normalizado']
        try:
            factor_val = pd.to_numeric(fila.get(factor_col), errors='coerce')
            if pd.notna(factor_val):
                datos['factor'] = float(factor_val)
            else:
                datos['factor'] = None
        except:
            datos['factor'] = None
    
    # Procesar fecha (opcional)
    if 'fecha' in columnas_detectadas:
        fecha_col = columnas_detectadas['fecha']['nombre_normalizado']
        try:
            fecha_val = pd.to_datetime(fila.get(fecha_col), errors='coerce')
            if pd.notna(fecha_val):
                datos['fecha_dato'] = fecha_val.date()
            else:
                datos['fecha_dato'] = None
        except:
            datos['fecha_dato'] = None
    
    return datos, errores


#
# --- ¡VISTA NUEVA AÑADIDA! (La Carga Masiva) ---
#
@login_required
def vista_carga_datos(request):
    # Verificar que existan clasificaciones
    clasificaciones_existentes = Clasificacion.objects.all()
    if not clasificaciones_existentes.exists():
        messages.warning(request, 
            'No hay clasificaciones creadas. Por favor crea al menos una clasificación antes de cargar datos.')
        return redirect('crear_clasificacion')
    
    if request.method == 'POST':
        form = CargaMasivaForm(request.POST, request.FILES)
        
        if form.is_valid():
            clasificacion_seleccionada = form.cleaned_data['clasificacion']
            archivo = form.cleaned_data['archivo_masivo']
            modo_carga = form.cleaned_data.get('modo_carga', 'crear')

            try:
                # Leer el archivo
                df = leer_archivo_excel(archivo)
                
                if df.empty:
                    messages.error(request, 'El archivo está vacío.')
                    return render(request, 'carga_datos.html', {'form': form})
                
                # Detectar columnas
                columnas_detectadas, columnas_no_detectadas, columnas_originales = detectar_columnas(df.copy())
                
                if 'nombre' in columnas_no_detectadas:
                    messages.error(request, 
                        f'No se pudo detectar la columna de nombre. '
                        f'Columnas encontradas: {", ".join(columnas_originales)}')
                    return render(request, 'carga_datos.html', {'form': form})
                
                # Procesar datos
                registros_creados = 0
                registros_actualizados = 0
                errores = []
                advertencias = []
                
                for index, fila in df.iterrows():
                    try:
                        datos, errores_fila = validar_fila_datos(fila, columnas_detectadas, index)
                        
                        if errores_fila:
                            errores.extend(errores_fila)
                            continue
                        
                        # Verificar si el registro ya existe (solo en modo actualizar)
                        if modo_carga == 'actualizar':
                            dato_existente = DatoTributario.objects.filter(
                                nombre_dato=datos['nombre_dato'],
                                clasificacion=clasificacion_seleccionada
                            ).first()
                            
                            if dato_existente:
                                # Actualizar registro existente
                                if 'monto' in datos:
                                    dato_existente.monto = datos['monto']
                                if 'factor' in datos:
                                    dato_existente.factor = datos['factor']
                                if 'fecha_dato' in datos:
                                    dato_existente.fecha_dato = datos['fecha_dato']
                                dato_existente.save()
                                registros_actualizados += 1
                            else:
                                # Crear nuevo registro
                                DatoTributario.objects.create(
                                    clasificacion=clasificacion_seleccionada,
                                    nombre_dato=datos['nombre_dato'],
                                    monto=datos.get('monto'),
                                    factor=datos.get('factor'),
                                    fecha_dato=datos.get('fecha_dato')
                                )
                                registros_creados += 1
                        else:
                            # Modo crear: siempre crear nuevo registro
                            DatoTributario.objects.create(
                                clasificacion=clasificacion_seleccionada,
                                nombre_dato=datos['nombre_dato'],
                                monto=datos.get('monto'),
                                factor=datos.get('factor'),
                                fecha_dato=datos.get('fecha_dato')
                            )
                            registros_creados += 1
                            
                    except Exception as e:
                        errores.append(f"Fila {index + 2}: {str(e)}")
                
                # Mensajes de resultado
                if registros_creados > 0:
                    messages.success(request, 
                        f'✅ Se crearon exitosamente {registros_creados} registro(s) nuevo(s).')
                
                if registros_actualizados > 0:
                    messages.info(request, 
                        f'🔄 Se actualizaron {registros_actualizados} registro(s) existente(s).')
                
                if errores:
                    # Limitar el número de errores mostrados
                    errores_mostrar = errores[:10]
                    mensaje_errores = f'❌ Se encontraron {len(errores)} error(es). '
                    if len(errores) > 10:
                        mensaje_errores += f'Mostrando los primeros 10:'
                    messages.error(request, mensaje_errores)
                    for error in errores_mostrar:
                        messages.error(request, f'  • {error}')
                
                if advertencias:
                    for advertencia in advertencias[:5]:
                        messages.warning(request, advertencia)
                
                return redirect('carga_datos') 

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado al procesar el archivo: {str(e)}")
                import traceback
                print(traceback.format_exc())

    else:
        form = CargaMasivaForm()

    # Obtener estadísticas de carga reciente
    ultimas_cargas = DatoTributario.objects.select_related('clasificacion').order_by('-creado_en')[:5]
    total_datos = DatoTributario.objects.count()

    context = {
        'form': form,
        'ultimas_cargas': ultimas_cargas,
        'total_datos': total_datos,
    }
    return render(request, 'carga_datos.html', context)

@login_required
def descargar_plantilla_excel(request):
    """Genera y descarga un archivo Excel de plantilla de ejemplo"""
    try:
        # Crear un DataFrame de ejemplo
        datos_ejemplo = {
            'Nombre': ['Ejemplo 1', 'Ejemplo 2', 'Ejemplo 3'],
            'Monto': [1000.50, 2500.75, 150.00],
            'Factor': [1.5, 2.3, 0.8],
            'Fecha': ['2024-01-15', '2024-02-20', '2024-03-10']
        }
        df = pd.DataFrame(datos_ejemplo)
        
        # Crear un buffer en memoria
        output = io.BytesIO()
        
        # Escribir el DataFrame al buffer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Datos')
            
            # Obtener la hoja de trabajo para formatear
            worksheet = writer.sheets['Datos']
            
            # Ajustar el ancho de las columnas
            try:
                from openpyxl.utils import get_column_letter
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    ) + 2
                    col_letter = get_column_letter(idx)
                    worksheet.column_dimensions[col_letter].width = min(max_length, 50)
            except:
                # Si hay error al formatear, continuar sin formato
                pass
        
        output.seek(0)
        
        # Crear la respuesta HTTP
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_carga_datos.xlsx"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar la plantilla: {str(e)}')
        return redirect('carga_datos')


@login_required
def vista_preview_archivo(request):
    """Vista para previsualizar el archivo antes de cargar (opcional, puede ser AJAX)"""
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        try:
            df = leer_archivo_excel(archivo)
            
            # Detectar columnas
            columnas_detectadas, columnas_no_detectadas, columnas_originales = detectar_columnas(df.copy())
            
            # Obtener las primeras 5 filas para preview
            preview_data = df.head(5).to_dict('records')
            
            return JsonResponse({
                'success': True,
                'total_filas': len(df),
                'columnas_detectadas': {
                    k: v['nombre_original'] for k, v in columnas_detectadas.items()
                },
                'columnas_no_detectadas': columnas_no_detectadas,
                'columnas_originales': columnas_originales,
                'preview': preview_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'No se proporcionó archivo'})


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