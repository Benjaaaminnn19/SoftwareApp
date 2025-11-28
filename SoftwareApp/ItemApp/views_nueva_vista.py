
@login_required
@user_passes_test(puede_gestionar_calificaciones, login_url='inicio')
def vista_ingresar_calificacion_manual(request):
    """Vista para ingresar una calificación tributaria manualmente"""
    
    if request.method == 'POST':
        form = CalificacionTributariaForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.creado_por = request.user
            calificacion.origen = 'CORREDOR' if tiene_rol(request.user, 'corredor') else 'TRIBUTARIO' if tiene_rol(request.user, 'tributario') else 'ADMIN'
            calificacion.save()
            messages.success(request, f'Calificación "{calificacion.instrumento}" ingresada exitosamente.')
            return redirect('modificar_calificacion', pk=calificacion.pk)
    else:
        form = CalificacionTributariaForm()
    
    # Obtener descripciones de factores para mostrar si es necesario
    from .forms import FACTOR_DESCRIPTIONS
    
    calificaciones_recientes = CalificacionTributaria.objects.filter(
        creado_por=request.user
    ).order_by('-creado_en')[:5]
    
    context = {
        'form': form,
        'calificaciones_recientes': calificaciones_recientes,
        'factor_descriptions': FACTOR_DESCRIPTIONS,
    }
    return render(request, 'calificaciones/ingresar_calificacion.html', context)
