from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class RegistroNUAM(models.Model):
    nombre_completo = models.CharField(max_length=255)
    email = models.EmailField(unique=True) 
    

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
    pais = models.CharField(max_length=100, choices=PAISES_CHOICES)
    
    identificador_tributario = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_completo


class Clasificacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre de la categoría (ej: Renta Fija, Renta Variable)")
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Clasificación"
        verbose_name_plural = "Clasificaciones"


class DatoTributario(models.Model):

    clasificacion = models.ForeignKey(
        Clasificacion, 
        on_delete=models.CASCADE,
        related_name="datos"
    )
    monto = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    

    factor = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    
    nombre_dato = models.CharField(max_length=255, help_text="Nombre o ID del dato")
    fecha_dato = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_dato} ({self.clasificacion.nombre})"

    class Meta:
        verbose_name = "Dato Tributario"
        verbose_name_plural = "Datos Tributarios"


class PerfilUsuario(models.Model):
    """Perfil de usuario con roles"""
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('corredor', 'Corredor'),
        ('tributario', 'Tributario'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='corredor')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        # Si es staff, asignar rol admin, sino corredor
        rol_inicial = 'admin' if instance.is_staff else 'corredor'
        PerfilUsuario.objects.get_or_create(user=instance, defaults={'rol': rol_inicial})


class CalificacionTributaria(models.Model):
    """Modelo para calificaciones tributarias"""
    
    MERCADO_CHOICES = [
        ('AC', 'AC'),
        ('ACCIONES', 'ACCIONES'),
        ('BONOS', 'BONOS'),
        ('FUTUROS', 'FUTUROS'),
    ]
    
    ORIGEN_CHOICES = [
        ('CORREDOR', 'CORREDOR'),
        ('TRIBUTARIO', 'TRIBUTARIO'),
        ('ADMIN', 'ADMIN'),
    ]
    
    # Campos principales
    mercado = models.CharField(max_length=50, choices=MERCADO_CHOICES, default='AC')
    instrumento = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_pago = models.DateField()
    secuencia_evento = models.CharField(max_length=50, unique=True)
    dividendo = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    valor_historico = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    factor_actualizacion = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    año = models.IntegerField()
    isfut = models.BooleanField(default=False)
    origen = models.CharField(max_length=50, choices=ORIGEN_CHOICES, default='CORREDOR')
    calificacion_pendiente = models.BooleanField(default=False)
    periodo_comercial = models.IntegerField(null=True, blank=True)
    evento_capital = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    
    # Factores tributarios
    factor_08 = models.DecimalField(max_digits=15, decimal_places=8, default=0, 
                                    verbose_name="Con crédito por IDPC generados a contar del 01.01.2017")
    factor_09 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con crédito por IDPC acumulados hasta el 31.12.2016")
    factor_10 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con derecho a crédito por pago IDPC Voluntario")
    factor_11 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin derecho a credito")
    factor_12 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Impto. 1ra Categ. Exento Gl Comp. Con Devolución")
    factor_13 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Impto. 1ra Categ. Afecto Gl Comp. Sin Devolución")
    factor_14 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Impto. 1ra Categ. Exento Gl Comp. Sin Devolución")
    factor_15 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Impto. Créditos pro Impuestos Externos")
    factor_16 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="No Constitutiva de Renta Acogido a Impto.")
    factor_17 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="No Constitutiva de Renta Devolución de Capital Art.17")
    factor_18 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Rentas Exentas de Impto. GC Y/O Impto Adicional")
    factor_19 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Ingreso no Constitutivos de Renta")
    factor_20 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin Derecho a Devolucion")
    factor_21 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con Derecho a Devolucion")
    factor_22 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin Derecho a Devolucion")
    factor_23 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con Derecho a Devolucion")
    factor_24 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin Derecho a Devolucion")
    factor_25 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con Derecho a Devolucion")
    factor_26 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin Derecho a Devolucion")
    factor_27 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con Derecho a Devolucion")
    factor_28 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Credito por IPE")
    factor_29 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin Derecho a Devolucion")
    factor_30 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con Derecho a Devolucion")
    factor_31 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Sin Derecho a Devolucion")
    factor_32 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Con Derecho a Devolucion")
    factor_33 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Credito por IPE")
    factor_34 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Cred. Por Impto. Tasa Adicional, Ex Art. 21 UR")
    factor_35 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="Tasa Efectiva Del Cred. Del FUT (TEF)")
    factor_36 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="TASA EFECTIVA DEL CRED. DEL FUNT (TEX)")
    factor_37 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                    verbose_name="DEVOLUCION DE CAPITAL ART. 17 NUM 7 UR")
    factor_198 = models.DecimalField(max_digits=15, decimal_places=8, default=0,
                                     verbose_name="Ingreso no Constitutivos de Renta")
    
    # Campos de auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='calificaciones_creadas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.año} - {self.instrumento} - {self.descripcion[:30]}"
    
    class Meta:
        verbose_name = "Calificación Tributaria"
        verbose_name_plural = "Calificaciones Tributarias"
        ordering = ['-año', '-fecha_pago', 'instrumento']
        indexes = [
            models.Index(fields=['año', 'instrumento']),
            models.Index(fields=['mercado', 'origen']),
            models.Index(fields=['calificacion_pendiente']),
        ]