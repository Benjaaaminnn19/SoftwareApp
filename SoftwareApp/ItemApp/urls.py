"""
URLs para ItemApp
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', vista_antepagina, name='antepagina'),
    path('registro/', views.vista_registro, name='registro'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.vista_logout, name='logout'),
    
    # Dashboard de usuarios
    path('inicio/', vista_inicio_usuario, name='inicio'),
    
    path('admin-panel/', vista_panel_administracion, name='admin_panel'),
    path('tributario-panel/', views.vista_panel_tributario, name='tributario_panel'),
    path('corredor-panel/', views.vista_panel_corredor, name='corredor_panel'),
    
    # Gestión de clasificaciones
    path('clasificacion/', views.vista_gestion_clasificacion, name='crear_clasificacion'),
    path('clasificacion/editar/<int:pk>/', views.vista_editar_clasificacion, name='editar_clasificacion'),
    path('clasificacion/eliminar/<int:pk>/', views.vista_eliminar_clasificacion, name='eliminar_clasificacion'),
    
    # Gestión de datos tributarios
    path('datos/cargar/', views.vista_carga_datos, name='carga_datos'),
    path('datos/listar/', views.vista_listar_datos_tributarios, name='listar_datos_tributarios'),
    path('datos/eliminar/<int:pk>/', views.vista_eliminar_dato_tributario, name='eliminar_dato_tributario'),
    path('datos/plantilla/', views.descargar_plantilla_excel, name='descargar_plantilla'),
    
    # Reportes
    path('reportes/', vista_reportes, name='reportes'),
    
    path('calificaciones/', vista_listar_calificaciones, name='listar_calificaciones'),
    path('calificaciones/ingresar/', views.vista_ingresar_calificacion, name='ingresar_calificacion'),
    path('calificaciones/modificar/<int:pk>/', views.vista_modificar_calificacion, name='modificar_calificacion'),
    path('calificaciones/eliminar/<int:pk>/', views.vista_eliminar_calificacion, name='eliminar_calificacion'),
    path('calificaciones/copiar/<int:pk>/', views.vista_copiar_calificacion, name='copiar_calificacion'),
]

