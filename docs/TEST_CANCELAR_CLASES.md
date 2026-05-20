# Guía de Prueba - Funcionalidad de Cancelar Clases

## Preparación

1. **Ejecutar la migración de base de datos** (en la carpeta `backend/`):
   ```bash
   python migrate_cancellations.py
   ```

2. **Reiniciar el backend** para que cargue los cambios:
   ```bash
   python app.py
   ```

## Escenario 1: Cancelación de Clase SIN Inscritos

### Pasos:
1. Acceder al Dashboard como **Admin** o **Empleado**
2. Verificar que haya al menos una clase "Activa" sin inscritos
3. Hacer click en botón **"Cancelar Clase"**
4. Confirmar en el diálogo de confirmación
5. **Resultado esperado**: 
   - Mensaje: "...cancelada exitosamente. El turno fue liberado..."
   - El estado de la clase cambia a **"Ya Cancelada"**
   - El botón se deshabilita

## Escenario 2: Cancelación de Clase CON Inscritos (Reserva Mensual)

### Preparación:
1. Crear una clase de Yoga para mañana a las 10:00
2. Inscribir como cliente mensual (tipo="Mensual")
3. Ir al Dashboard como Admin/Empleado

### Pasos:
1. Hacer click en **"Cancelar Clase"** 
2. Confirmar en el diálogo
3. **Resultado esperado**:
   - Mensaje: "...Se asignaron 1 créditos a alumnos de reserva mensual válidos por 30 días"
   - El cliente debe recibir 1 crédito en su tabla `creditos`
   - El crédito tiene `estado="Disponible"` y `fecha_expiracion` en 30 días

### Verificar en Base de Datos:
```sql
SELECT * FROM creditos WHERE estado="Disponible";
```

## Escenario 3: Cancelación de Clase CON Inscritos (Reserva Suelta)

### Preparación:
1. Crear una clase de Pilates para mañana a las 14:00
2. Inscribir como cliente suelto (tipo="Suelta")
3. Ir al Dashboard como Admin/Empleado

### Pasos:
1. Hacer click en **"Cancelar Clase"**
2. Confirmar en el diálogo
3. **Resultado esperado**:
   - Mensaje: "...Se marcaron 1 reembolsos para alumnos de reserva suelta"
   - La inscripción debe tener `requiere_reembolso=True`

### Verificar en Base de Datos:
```sql
SELECT * FROM enrollments WHERE requiere_reembolso=1;
```

## Escenario 4: Validar que Clases Canceladas NO Aparecen en Catálogo

### Pasos:
1. Crear una clase Activa para hoy
2. Cancelarla desde el Dashboard
3. Ir a **Actividades** (catálogo cliente)
4. **Resultado esperado**:
   - La clase cancelada NO aparece en el catálogo disponible
   - Solo las clases con `estado="Activa"` se muestran

## Validaciones de Seguridad

### No puede cancelar un cliente regular:
1. Logout como Admin
2. Login como cliente
3. Intentar acceder a `/api/classes/1/cancelar`
4. **Resultado esperado**: Error 403 "No tienes permisos de personal para cancelar clases"

### No puede cancelar dos veces:
1. Cancelar una clase
2. Intentar cancelarla de nuevo
3. **Resultado esperado**: Error 400 "Esta clase ya fue cancelada"

## Campos en Base de Datos

### Tabla `classes`:
```sql
ALTER TABLE classes ADD COLUMN estado VARCHAR(20) DEFAULT 'Activa';
-- Valores válidos: 'Activa', 'Cancelada'
```

### Tabla `enrollments`:
```sql
ALTER TABLE enrollments ADD COLUMN tipo VARCHAR(20) DEFAULT 'Suelta';
ALTER TABLE enrollments ADD COLUMN estado VARCHAR(20) DEFAULT 'Activa';
ALTER TABLE enrollments ADD COLUMN requiere_reembolso BOOLEAN DEFAULT 0;
-- tipo: 'Mensual' (pago de suscripción), 'Suelta' (pago por clase)
-- estado: 'Activa', 'Cancelada'
```

## Notas de Implementación

- ✅ Endpoint: `POST /api/classes/<clase_id>/cancelar`
- ✅ Autenticación: Requerida (admin o employee)
- ✅ Créditos: Sistema de 30 días con fecha_expiracion
- ✅ Reembolsos: Marcados para procesamiento posterior
- ✅ UI: DashboardView.vue muestra estado actualizado en tiempo real
