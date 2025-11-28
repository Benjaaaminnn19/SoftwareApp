# Guía de Uso: Roles de Usuario y Carga Manual de Calificaciones

## 📋 Tabla de Contenidos
1. [Crear Usuarios con Roles](#crear-usuarios-con-roles)
2. [Carga Manual de Calificaciones](#carga-manual-de-calificaciones)
3. [Roles Disponibles](#roles-disponibles)
4. [Acceso por Rol](#acceso-por-rol)

---

## 🔐 Crear Usuarios con Roles

### Opción 1: Crear 3 usuarios predefinidos automáticamente

Ejecuta este comando desde la carpeta `SoftwareApp`:

```bash
cd SoftwareApp
python manage.py crear_usuarios_roles --crear-predefinidos
```

Esto creará automáticamente 3 usuarios:

| Usuario | Email | Contraseña | Rol |
|---------|-------|------------|-----|
| `admin_user` | admin@example.com | AdminPass123! | Admin |
| `tributario_user` | tributario@example.com | TributarioPass123! | Tributario |
| `corredor_user` | corredor@example.com | CorredorPass123! | Corredor |

### Opción 2: Crear un usuario individual

```bash
python manage.py crear_usuarios_roles \
  --username nombreusuario \
  --email usuario@example.com \
  --password MiPassword123! \
  --rol tributario
```

**Parámetros:**
- `--username`: Nombre de usuario (requerido)
- `--email`: Email del usuario (requerido)
- `--password`: Contraseña (requerido)
- `--rol`: Puede ser `admin`, `tributario` o `corredor` (default: `corredor`)

---

## 📊 Roles Disponibles

### 👨‍💼 Admin (Administrador)
- Acceso total al panel de administración
- Crear, editar y eliminar clasificaciones
- Gestionar usuarios
- Crear, modificar y eliminar calificaciones tributarias
- Ver reportes completos
- Crear carga masiva de datos

### 💰 Tributario (Usuario Tributario)
- Acceso a ingreso de calificaciones tributarias
- Puede crear, modificar calificaciones que él creó
- Ver reportes de calificaciones
- No puede eliminar calificaciones (solo admin)
- No puede gestionar usuarios

### 🏪 Corredor (Usuario Corredor)
- Acceso a ingreso de calificaciones tributarias
- Puede crear, modificar calificaciones que él creó
- Ver reportes de calificaciones
- No puede eliminar calificaciones (solo admin)
- No puede gestionar usuarios

---

## 📝 Carga Manual de Calificaciones

### Acceso
```
URL: http://localhost:8000/calificaciones/ingresar/
o
http://softwareapp-production.up.railway.app/calificaciones/ingresar/
```

### Campos Principales del Formulario

#### 1. Datos Básicos
- **Mercado**: Selecciona el tipo de mercado (AC, ACCIONES, BONOS, FUTUROS)
- **Instrumento**: Código o nombre del instrumento (ej: ACME, BAP)
- **Descripción**: Descripción del evento (ej: "DIVIDENDO DE PRUEBA 1.54")

#### 2. Fechas y Eventos
- **Fecha Pago**: Fecha en formato DD-MM-YYYY
- **Secuencia Evento**: Identificador único del evento (ej: 100000807)

#### 3. Montos
- **Dividendo**: Monto del dividendo (ej: 0.54)
- **Valor Histórico**: Valor histórico del instrumento (ej: 0.00000000)
- **Factor de Actualización**: Factor de actualización (ej: 0)

#### 4. Información Adicional
- **Año**: Año fiscal (ej: 2025)
- **ISFUT**: Marcar si es aplicable

### Ejemplo de Carga

```
Mercado:                    AC
Instrumento:                ACME
Descripción:                DIVIDENDO DE PRUEBA 1.54
Fecha Pago:                 01-04-2025
Secuencia Evento:           100000807
Dividendo:                  0.00000154
Valor Histórico:            0.00000000
Factor de Actualización:    0
Año:                        2025
ISFUT:                      ☐ (sin marcar)
```

### Flujo de Carga

1. **Ingresar Calificación**: Completa el formulario con los datos básicos
   - Click en "INGRESAR"
   - Se crea la calificación con estado "Pendiente de Calificación"

2. **Modificar Calificación** (Opcional): Agrega factores tributarios
   - Sistema redirige automáticamente a la vista de modificación
   - Aquí puedes agregar hasta 37 factores tributarios diferentes
   - Guardar cambios

3. **Listar y Buscar**: Ve al menú de Calificaciones para ver todas las ingresadas
   - Filtrar por mercado, origen, año
   - Copiar calificaciones existentes
   - Modificar o eliminar (si eres admin)

---

## 🎯 Acceso por Rol

### Rutas Disponibles por Rol

#### Para ADMIN
```
/admin-panel/                           → Panel de administración
/clasificacion/                         → Gestionar clasificaciones
/datos/cargar/                          → Carga masiva de datos
/datos/listar/                          → Listar datos tributarios
/calificaciones/                        → Listar calificaciones
/calificaciones/ingresar/               → Ingresar calificación
/calificaciones/modificar/<id>/         → Modificar calificación
/calificaciones/eliminar/<id>/          → Eliminar calificación
/reportes/                              → Ver reportes
```

#### Para TRIBUTARIO y CORREDOR
```
/inicio/                                → Dashboard personal
/calificaciones/                        → Listar calificaciones
/calificaciones/ingresar/               → Ingresar calificación
/calificaciones/modificar/<id>/         → Modificar propia calificación
/reportes/                              → Ver reportes
```

---

## 💡 Tips y Recomendaciones

### Seguridad
- 🔒 Cambia la contraseña predeterminada después del primer login
- 🔐 No compartas credenciales con otros usuarios
- 🔑 Guarda tus credenciales en un lugar seguro

### Carga de Datos
- 📋 Usa la plantilla Excel para carga masiva (`/datos/plantilla/`)
- ✅ Verifica los datos antes de ingresar
- 🔄 Puedes copiar calificaciones existentes y modificarlas
- 💾 Todos los cambios se guardan automáticamente

### Mejor Práctica para Calificaciones
```
1. Ingresar calificación básica
2. Sistema redirige a modificación
3. Agregar factores tributarios si es necesario
4. Guardar cambios
5. Usar "Copiar" para crear variantes
```

---

## 🐛 Troubleshooting

### Error: "usuario ya existe"
```bash
# El usuario ya está en la base de datos
# Opción 1: Usar otro nombre de usuario
# Opción 2: Eliminar el usuario y recrearlo desde Django admin
```

### Error: "No puedo acceder a crear calificaciones"
- Verifica que tu rol no sea "corredor"
- Contacta al administrador para cambiar tu rol

### Las calificaciones no se guardan
- Verifica que todos los campos requeridos estén completos
- Comprueba los errores mostrados en rojo bajo cada campo

---

## 📞 Soporte

Para más información o ayuda:
1. Revisa el panel de admin en `/admin/`
2. Consulta los logs de la aplicación
3. Contacta al equipo de desarrollo

---

**Última actualización**: 2025-11-27
**Versión**: 1.0
