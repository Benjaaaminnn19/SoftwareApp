
# ============================================================================
# PANELES ESPECÍFICOS POR ROL
# ============================================================================

@login_required
@user_passes_test(lambda u: tiene_rol(u, 'tributario'), login_url='inicio')
def vista_panel_tributario(request):
    """Panel especializado para usuarios Tributario"""
    
    # Estadísticas personales
    mis_calificaciones = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).count()
    
    calificaciones_pendientes = CalificacionTributaria.objects.filter(
        creado_por=request.user,
        calificacion_pendiente=True
    ).count()
    
    # Últimas calificaciones creadas por el usuario
    ultimas_calificaciones = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).order_by('-creado_en')[:10]
    
    # Estadísticas por origen
    stats_origen = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).values('origen').annotate(
        total=Count('id')
    )
    
    # Estadísticas por año
    stats_por_ano = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).values('año').annotate(
        total=Count('id')
    ).order_by('-año')
    
    context = {
        'mis_calificaciones': mis_calificaciones,
        'calificaciones_pendientes': calificaciones_pendientes,
        'ultimas_calificaciones': ultimas_calificaciones,
        'stats_origen': stats_origen,
        'stats_por_ano': stats_por_ano,
    }
    
    return render(request, 'tributario_panel.html', context)


@login_required
@user_passes_test(lambda u: tiene_rol(u, 'corredor'), login_url='inicio')
def vista_panel_corredor(request):
    """Panel especializado para usuarios Corredor"""
    
    # Estadísticas personales
    mis_calificaciones = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).count()
    
    calificaciones_pendientes = CalificacionTributaria.objects.filter(
        creado_por=request.user,
        calificacion_pendiente=True
    ).count()
    
    # Últimas calificaciones creadas por el usuario
    ultimas_calificaciones = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).order_by('-creado_en')[:10]
    
    # Estadísticas por mercado
    stats_mercado = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).values('mercado').annotate(
        total=Count('id')
    )
    
    # Estadísticas por año
    stats_por_ano = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).values('año').annotate(
        total=Count('id')
    ).order_by('-año')
    
    context = {
        'mis_calificaciones': mis_calificaciones,
        'calificaciones_pendientes': calificaciones_pendientes,
        'ultimas_calificaciones': ultimas_calificaciones,
        'stats_mercado': stats_mercado,
        'stats_por_ano': stats_por_ano,
    }
    
    return render(request, 'corredor_panel.html', context)
