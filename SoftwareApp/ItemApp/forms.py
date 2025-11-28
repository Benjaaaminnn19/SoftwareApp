from django import forms
from django.contrib.auth.models import User 
from .models import RegistroNUAM, Clasificacion, CalificacionTributaria, PerfilUsuario
import datetime

PAISES_CHOICES = [
    ('chile', 'Chile'),
    ('colombia', 'Colombia'),
    ('peru', 'Perú'),
    ('argentina', 'Argentina'),
    ('mexico', 'México'),
    ('brasil', 'Brasil'),
    ('ecuador', 'Ecuador'),
    ('venezuela', 'Venezuela'),
    ('uruguay', 'Uruguay'),
    ('paraguay', 'Paraguay'),
    ('bolivia', 'Bolivia'),
]

class RegistroNUAMForm(forms.Form):
    nombre_completo = forms.CharField(
        label='Nombre Completo', 
        max_length=255, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Contraseña', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    pais = forms.ChoiceField(
        choices=PAISES_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    identificador_tributario = forms.CharField(
        label='Identificador Tributario', 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_nacimiento = forms.DateField(
        label='Fecha de Nacimiento', 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = datetime.date.today()
            age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            if age < 18:
                raise forms.ValidationError("Debes ser mayor de 18 años para registrarte.")
        return fecha_nacimiento
    
class ClasificacionForm(forms.ModelForm):
    class Meta:
        model = Clasificacion
        fields = ['nombre'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre de la Clasificación',
        }


class CargaMasivaForm(forms.Form):
    
    clasificacion = forms.ModelChoiceField(
        queryset=Clasificacion.objects.all(),
        label="Seleccionar Clasificación",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Selecciona la clasificación a la que pertenecen los datos"
    )
    
    archivo_masivo = forms.FileField(
        label="Cargar Archivo (Excel o CSV)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls',
            'id': 'archivo_masivo'
        }),
        help_text="Formatos soportados: .csv, .xlsx, .xls (Máximo 10MB)"
    )
    
    modo_carga = forms.ChoiceField(
        choices=[
            ('crear', 'Crear nuevos registros'),
            ('actualizar', 'Actualizar registros existentes (por nombre)'),
        ],
        initial='crear',
        label="Modo de Carga",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text="Elige si quieres crear nuevos registros o actualizar los existentes"
    )
    
    def clean_archivo_masivo(self):
        archivo = self.cleaned_data.get('archivo_masivo')
        if archivo:
            # Validar tamaño (10MB máximo)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError("El archivo es demasiado grande. El tamaño máximo es 10MB.")
            
            # Validar extensión
            nombre = archivo.name.lower()
            if not (nombre.endswith('.csv') or nombre.endswith('.xlsx') or nombre.endswith('.xls')):
                raise forms.ValidationError("Formato de archivo no soportado. Use .csv, .xlsx o .xls")
        
        return archivo


# ============================================================================
# FORMULARIOS PARA CALIFICACIONES TRIBUTARIAS
# ============================================================================

class CalificacionTributariaForm(forms.ModelForm):
    """Formulario para ingresar una nueva calificación tributaria"""
    
    class Meta:
        model = CalificacionTributaria
        fields = [
            'mercado', 'instrumento', 'descripcion', 'fecha_pago', 
            'secuencia_evento', 'dividendo', 'valor_historico', 
            'factor_actualizacion', 'año', 'isfut'
        ]
        widgets = {
            'mercado': forms.Select(attrs={'class': 'form-control'}),
            'instrumento': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'DD-MM-YYYY'
            }),
            'secuencia_evento': forms.TextInput(attrs={'class': 'form-control'}),
            'dividendo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'valor_historico': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'factor_actualizacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            'isfut': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'mercado': 'Mercado',
            'instrumento': 'Instrumento',
            'descripcion': 'Descripción',
            'fecha_pago': 'Fecha Pago',
            'secuencia_evento': 'Secuencia Evento',
            'dividendo': 'Dividendo',
            'valor_historico': 'Valor Histórico',
            'factor_actualizacion': 'Factor de Actualización',
            'año': 'Año',
            'isfut': 'ISFUT',
        }


# Construir widgets y labels para factores
FACTOR_WIDGETS = {}
FACTOR_LABELS = {}
FACTOR_DESCRIPTIONS = {}

# Widgets para factores
for i in range(8, 38):
    FACTOR_WIDGETS[f'factor_{i:02d}'] = forms.NumberInput(attrs={
        'class': 'form-control',
        'step': '0.00000001'
    })
FACTOR_WIDGETS['factor_198'] = forms.NumberInput(attrs={
    'class': 'form-control',
    'step': '0.00000001'
})

# Descripciones para factores (se usa para labels y para mostrar en templates)
FACTOR_DESCRIPTIONS_DICT = {
    8: 'Con crédito por IDPC generados a contar del 01.01.2017',
    9: 'Con crédito por IDPC acumulados hasta el 31.12.2016',
    10: 'Con derecho a crédito por pago IDPC Voluntario',
    11: 'Sin derecho a credito',
    12: 'Impto. 1ra Categ. Exento Gl Comp. Con Devolución',
    13: 'Impto. 1ra Categ. Afecto Gl Comp. Sin Devolución',
    14: 'Impto. 1ra Categ. Exento Gl Comp. Sin Devolución',
    15: 'Impto. Créditos pro Impuestos Externos',
    16: 'No Constitutiva de Renta Acogido a Impto.',
    17: 'No Constitutiva de Renta Devolución de Capital Art.17',
    18: 'Rentas Exentas de Impto. GC Y/O Impto Adicional',
    19: 'Ingreso no Constitutivos de Renta',
    20: 'Sin Derecho a Devolucion',
    21: 'Con Derecho a Devolucion',
    22: 'Sin Derecho a Devolucion',
    23: 'Con Derecho a Devolucion',
    24: 'Sin Derecho a Devolucion',
    25: 'Con Derecho a Devolucion',
    26: 'Sin Derecho a Devolucion',
    27: 'Con Derecho a Devolucion',
    28: 'Credito por IPE',
    29: 'Sin Derecho a Devolucion',
    30: 'Con Derecho a Devolucion',
    31: 'Sin Derecho a Devolucion',
    32: 'Con Derecho a Devolucion',
    33: 'Credito por IPE',
    34: 'Cred. Por Impto. Tasa Adicional, Ex Art. 21 UR',
    35: 'Tasa Efectiva Del Cred. Del FUT (TEF)',
    36: 'TASA EFECTIVA DEL CRED. DEL FUNT (TEX)',
    37: 'DEVOLUCION DE CAPITAL ART. 17 NUM 7 UR',
    198: 'Ingreso no Constitutivos de Renta',
}

for num in FACTOR_DESCRIPTIONS_DICT.keys():
    field_name = f'factor_{num:02d}' if num != 198 else 'factor_198'
    FACTOR_LABELS[field_name] = f'Factor-{num:02d}' if num != 198 else 'Factor-198'
    FACTOR_DESCRIPTIONS[field_name] = FACTOR_DESCRIPTIONS_DICT[num]


class ModificarCalificacionTributariaForm(forms.ModelForm):
    """Formulario completo para modificar una calificación tributaria con todos los factores"""
    
    class Meta:
        model = CalificacionTributaria
        fields = [
            # Campos principales
            'mercado', 'instrumento', 'valor_historico', 'fecha_pago', 
            'evento_capital', 'descripcion', 'secuencia_evento', 'año',
            # Todos los factores
            'factor_08', 'factor_09', 'factor_10', 'factor_11', 'factor_12', 'factor_13',
            'factor_14', 'factor_15', 'factor_16', 'factor_17', 'factor_18', 'factor_19',
            'factor_20', 'factor_21', 'factor_22', 'factor_23', 'factor_24', 'factor_25',
            'factor_26', 'factor_27', 'factor_28', 'factor_29', 'factor_30', 'factor_31',
            'factor_32', 'factor_33', 'factor_34', 'factor_35', 'factor_36', 'factor_37',
            'factor_198'
        ]
        widgets = {
            'mercado': forms.Select(attrs={'class': 'form-control'}),
            'instrumento': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_historico': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'evento_capital': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.00000001'
            }),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'secuencia_evento': forms.TextInput(attrs={'class': 'form-control'}),
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            **FACTOR_WIDGETS
        }
        labels = {
            'mercado': 'Mercado',
            'instrumento': 'Instrumento',
            'valor_historico': 'Valor Histórico',
            'fecha_pago': 'Fecha Pago',
            'evento_capital': 'Evento Capital',
            'descripcion': 'Descripción',
            'secuencia_evento': 'Secuencia Evento',
            'año': 'Año',
            **FACTOR_LABELS
        }