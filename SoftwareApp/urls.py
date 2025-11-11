# SoftwareApp/urls.py
from django.contrib import admin
from django.urls import path
from ItemApp import views as item_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # ============================================
    # VISTAS PÚBLICAS
    # ============================================
    path('', item_views.vista_antepagina, name='antepagina'),
    path('registro/', item_views.vista_registro, name='registro'),
    path('login/', item_views.CustomLoginView.as_view(), name='login'),
    path('logout/', item_views.vista_logout, name='logout'),
    
    # ============================================
    # VISTA PRINCIPAL (Redirige según tipo de usuario)
    # ============================================
    # Usuarios regulares van a 'inicio' (dashboard simplificado)
    path('inicio/', item_views.vista_inicio_usuario, name='inicio'),
    
    # ============================================
    # PANEL DE ADMINISTRACIÓN (SOLO STAFF)
    # ============================================
    path('admin-panel/', item_views.vista_panel_administracion, name='admin_panel'),
    
    # ============================================
    # GESTIÓN DE CLASIFICACIONES (Todos los usuarios autenticados)
    # ============================================
    path('clasificacion/', item_views.vista_gestion_clasificacion, name='crear_clasificacion'),
    path('clasificacion/editar/<int:pk>/', item_views.vista_editar_clasificacion, name='editar_clasificacion'),
    path('clasificacion/eliminar/<int:pk>/', item_views.vista_eliminar_clasificacion, name='eliminar_clasificacion'),
    
    # ============================================
    # CARGA Y GESTIÓN DE DATOS (Todos los usuarios autenticados)
    # ============================================
    path('carga-datos/', item_views.vista_carga_datos, name='carga_datos'),
    path('carga-datos/plantilla/', item_views.descargar_plantilla_excel, name='descargar_plantilla'),
    path('datos-tributarios/', item_views.vista_listar_datos_tributarios, name='listar_datos_tributarios'),
    path('datos-tributarios/eliminar/<int:pk>/', item_views.vista_eliminar_dato_tributario, name='eliminar_dato_tributario'),
]