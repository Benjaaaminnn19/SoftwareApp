from django.contrib import admin
from .models import RegistroNUAM, Clasificacion, DatoTributario, PerfilUsuario, CalificacionTributaria


@admin.register(RegistroNUAM)
class RegistroNUAMAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'email', 'pais', 'identificador_tributario', 'fecha_nacimiento', 'creado_en')
    list_filter = ('pais', 'creado_en')
    search_fields = ('nombre_completo', 'email', 'identificador_tributario')
    readonly_fields = ('creado_en',)
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)


@admin.register(Clasificacion)
class ClasificacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creado_en', 'total_datos')
    search_fields = ('nombre',)
    readonly_fields = ('creado_en',)
    date_hierarchy = 'creado_en'
    
    def total_datos(self, obj):
        return obj.datos.count()
    total_datos.short_description = 'Total de Datos'


@admin.register(DatoTributario)
class DatoTributarioAdmin(admin.ModelAdmin):
    list_display = ('nombre_dato', 'clasificacion', 'monto', 'factor', 'fecha_dato', 'creado_en')
    list_filter = ('clasificacion', 'fecha_dato', 'creado_en')
    search_fields = ('nombre_dato',)
    readonly_fields = ('creado_en',)
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)
    list_per_page = 50


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'creado_en')
    list_filter = ('rol', 'creado_en')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('creado_en', 'actualizado_en')


@admin.register(CalificacionTributaria)
class CalificacionTributariaAdmin(admin.ModelAdmin):
    list_display = ('año', 'instrumento', 'mercado', 'fecha_pago', 'descripcion', 'origen', 'calificacion_pendiente')
    list_filter = ('mercado', 'origen', 'año', 'calificacion_pendiente', 'isfut', 'creado_en')
    search_fields = ('instrumento', 'descripcion', 'secuencia_evento')
    readonly_fields = ('creado_en', 'actualizado_en', 'creado_por')
    date_hierarchy = 'fecha_pago'
    ordering = ('-año', '-fecha_pago')
    list_per_page = 50
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('mercado', 'instrumento', 'descripcion', 'fecha_pago', 'secuencia_evento', 
                      'año', 'periodo_comercial', 'origen', 'calificacion_pendiente')
        }),
        ('Valores', {
            'fields': ('dividendo', 'valor_historico', 'factor_actualizacion', 'evento_capital', 'isfut')
        }),
        ('Factores Tributarios (08-13)', {
            'fields': ('factor_08', 'factor_09', 'factor_10', 'factor_11', 'factor_12', 'factor_13')
        }),
        ('Factores Tributarios (14-19)', {
            'fields': ('factor_14', 'factor_15', 'factor_16', 'factor_17', 'factor_18', 'factor_19')
        }),
        ('Factores Tributarios (20-25)', {
            'fields': ('factor_20', 'factor_21', 'factor_22', 'factor_23', 'factor_24', 'factor_25')
        }),
        ('Factores Tributarios (26-31)', {
            'fields': ('factor_26', 'factor_27', 'factor_28', 'factor_29', 'factor_30', 'factor_31')
        }),
        ('Factores Tributarios (32-37, 198)', {
            'fields': ('factor_32', 'factor_33', 'factor_34', 'factor_35', 'factor_36', 'factor_37', 'factor_198')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'creado_en', 'actualizado_en')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
