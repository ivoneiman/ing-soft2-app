Épicas identificadas
E1: Autenticación y gestión de usuarios: Registro, login con mail (diferenciando roles como cliente, admin, recepcionista, admin financiero y super admin para los dueños)

**Historias de usuario**
1. Como **cliente**, quiero **registrarme con mi email y una contraseña** para **acceder al sistema y reservar clases**.
2. Como **cliente**, quiero **iniciar sesión con mi email y contraseña** para **ver mis reservas y datos personales**.
3. Como **admin**, quiero **crear, editar y desactivar cuentas de usuarios** para **gestionar el acceso al sistema**.
4. Como **recepcionista**, quiero **asignar roles a nuevos usuarios** para **controlar los permisos según su función**.
5. Como **admin financiero**, quiero **visualizar y exportar datos de pagos** para **realizar conciliaciones y reportes**.
6. Como **super admin**, quiero **tener control total sobre la configuración del sistema** para **garantizar la seguridad y el cumplimiento de políticas**.
E2: Gestión de clases y turnos: creación, edición y cancelación de clases. (definir horarios, cupos máximos y actividades)

**Historias de usuario**
1. Como **admin**, quiero **crear una nueva clase especificando actividad, horario y cupo máximo** para **ofrecerla a los clientes**.
2. Como **admin**, quiero **editar los datos de una clase existente** para **ajustar horarios o cupos según necesidad**.
3. Como **admin**, quiero **cancelar una clase** y **notificar automáticamente a los clientes inscritos** para **evitar ausencias inesperadas**.
4. Como **profesor**, quiero **ver el listado de mis clases programadas** para **prepararme adecuadamente**.
5. Como **recepcionista**, quiero **asignar o reasignar profesores a clases** para **garantizar la cobertura de horarios**.
E3: Inscripción a clases: los clientes pueden ver clases “disponibles” e inscribirse o darse de baja de sus turnos

**Historias de usuario**
1. Como **cliente**, quiero **consultar el catálogo de clases disponibles** para **elegir la que mejor se ajuste a mi horario**.
2. Como **cliente**, quiero **inscribirme en una clase con cupo disponible** para **reservar mi lugar**.
3. Como **cliente**, quiero **cancelar mi inscripción antes de la fecha límite** para **liberar el cupo a otros usuarios**.
4. Como **cliente**, quiero **recibir confirmación por email o notificación** al inscribirme o cancelar, para **tener constancia de mi reserva**.
E4: Control de asistencia: Pasar lista digital” cuando ingresen los clientes a su clase asignada

**Historias de usuario**
1. Como **profesor**, quiero **marcar la asistencia de los clientes al iniciar la clase** para **llevar registro preciso**.
2. Como **admin**, quiero **visualizar reportes de asistencia por clase y por cliente** para **identificar ausencias recurrentes**.
3. Como **recepcionista**, quiero **consultar la lista de asistencia en tiempo real** para **atender consultas de clientes**.
E5: Gestión de pagos: registro de pagos por actividad mensual. Ya sea tarjeta o mercadopago. (sistema de descuentos y créditos?) - Clase de prueba ($)

**Historias de usuario**
1. Como **cliente**, quiero **pagar mi suscripción mensual con tarjeta o Mercado Pago** para **acceder a las clases contratadas**.
2. Como **cliente**, quiero **ver el historial de mis pagos** para **verificar que se hayan registrado correctamente**.
3. Como **admin financiero**, quiero **generar resúmenes mensuales de pagos** para **realizar la contabilidad**.
4. Como **admin financiero**, quiero **configurar descuentos según la fecha de pago o créditos** para **ofrecer promociones**.
5. Como **admin**, quiero **definir el precio de una clase de prueba** y **permitir su compra única** para **atraer nuevos clientes**.
E6: Notificaciones: avisos automáticos a clientes ante cancelación de clase

**Historias de usuario**
1. Como **cliente**, quiero **recibir una notificación (email/SMS/WhatsApp) cuando una clase que tengo reservada sea cancelada** para **reprogramar o buscar alternativa**.
2. Como **admin**, quiero **configurar plantillas de notificación y canales de envío** para **automatizar la comunicación**.
3. Como **profesor**, quiero **activar/desactivar notificaciones para mis clases** según la política del centro.
E7: Reportes: resúmenes mensuales de pagos, ¿historial de clases y asistencia para admins?

**Historias de usuario**
1. Como **admin financiero**, quiero **obtener un reporte mensual de ingresos por actividad** para **analizar la rentabilidad**.
2. Como **admin**, quiero **ver un historial de clases impartidas y asistencia** para **evaluar la ocupación y desempeño de los profesores**.
3. Como **recepcionista**, quiero **consultar reportes de asistencia por día** para **optimizar la gestión de recursos**.
E8: Panel administrativo: Interfaz para los admin que permita gestionar usuarios, clases, pagos y generar reportes.

**Historias de usuario**
1. Como **admin**, quiero **acceder a un panel donde pueda crear, editar y eliminar usuarios** para **mantener el control de acceso**.
2. Como **admin**, quiero **gestionar el catálogo de clases (crear, modificar, cancelar)** desde una única interfaz para **simplificar la administración**.
3. Como **admin financiero**, quiero **visualizar y exportar reportes de pagos y asistencia** desde el panel para **facilitar la toma de decisiones**.
4. Como **admin**, quiero **configurar roles y permisos** para **garantizar que cada usuario tenga acceso solo a lo necesario**.