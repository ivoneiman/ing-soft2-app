<template>
  <div class="gestion-clases-container">
    <h1 class="titulo-principal">INFORMACIÓN DE CLASES</h1>
    <p class="descripcion-panel">Panel de control para visualizar, monitorear y gestionar las clases.</p>

    <div class="tarjeta-oscura-tabla">
      <div class="tabla-encabezado">
        <h2 class="subtitulo-seccion" style="margin: 0; border: none; padding: 0;">Seleccionar Clase</h2>
      </div>

      <p v-if="feedbackMessage" :class="['feedback-message', feedbackType]">
        {{ feedbackMessage }}
      </p>

      <p v-if="cargando" class="loading-text">Cargando clases desde el servidor...</p>

      <p v-else-if="allClasses.length === 0" class="empty-state">
        No se encuentran clases registradas en el sistema.
      </p>

      <div v-else>
        <div class="filtros-contenedor">
        <div class="form-group">
          <label for="status">Estado</label>
          <select id="status" v-model="selectedStatus">
            <option value="Todas">Todas las clases</option>
            <option value="Activa"> Activas</option>
            <option value="Finalizada"> Finalizadas</option>
            <option value="Cancelada"> Canceladas</option>
          </select>
        </div>
        <div class="form-group">
          <label for="month">Mes</label>
          <select id="month" v-model="selectedMonth">
            <option value="">Todos los meses</option>
            <option v-for="month in availableMonths" :key="month.value" :value="month.value">
              {{ month.label }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="day">Día</label>
          <select id="day" v-model="selectedDay">
            <option value="">Todos los días</option>
            <option v-for="day in 31" :key="day" :value="day">{{ day }}</option>
          </select>
        </div>
        <div class="form-group">
          <label for="activity">Actividad</label>
          <select id="activity" v-model="selectedActivityName">
            <option value="">Todas las actividades</option>
            <option v-for="activity in availableActivities" :key="activity" :value="activity">
              {{ activity }}
            </option>
          </select>
        </div>
        </div>
      <div v-if="displayedClasses.length > 0" class="tabla-responsiva-contenedor mt-4">
        <table class="tabla-gestion-gym">
          <thead>
            <tr>
              <th>Actividad</th>
              <th>Día</th>
              <th>Mes</th>
              <th>Horario</th>
              <th>Sala</th>
              <th>Profesor</th>
              <th>Cupos Ocupados</th>
              <th>Estado</th>
              <th style="text-align: center; width: 320px;">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="clase in displayedClasses" 
              :key="clase.id" 
              :class="{ 'fila-cancelada': isCancelled(clase) }"
            >
              <td class="col-actividad">{{ clase.actividad || clase.name }}</td>
              <td class="texto-celda">{{ formatDay(clase.fecha_hora) }}</td>
              <td class="texto-celda">{{ formatMonth(clase.fecha_hora) }}</td>
              <td class="texto-celda">{{ formatTime(clase.fecha_hora) }}</td>
              <td class="texto-celda">{{ clase.room || 'N/A' }}</td>
              <td class="texto-celda">{{ clase.profesor_nombre || 'N/A' }}</td>
              <td class="texto-celda">{{ clase.enrolled }} / {{ clase.cupoMaximo }}</td>
              <td>
                <span :class="isCancelled(clase) ? 'etiqueta-estado-roja' : 'etiqueta-estado-verde'">
                  {{ getDisplayStatus(clase) }}
                </span>
              </td>
              <td style="text-align: center;">
                <div v-if="getDisplayStatus(clase) === 'Activa'" class="acciones-columna">
                  <button
                    @click="abrirModalEdicion(clase)"
                    class="btn-tabla-editar"
                  >
                    Editar</button>
                  <button
                    @click="goToAttendance(clase.id)"
                    class="btn-tabla-asistencia"
                  >
                    Pasar asistencia
                  </button>
                  <button 
                    @click="abrirConfirmacionCancelacion(clase)"
                    :disabled="isCancelled(clase)"
                    class="btn-tabla-cancelar"
                    :class="{ 'btn-tabla-deshabilitado': isCancelled(clase) }"
                  >
                    Cancelar
                  </button>
                </div>
                <div v-else-if="getDisplayStatus(clase) === 'Finalizada'">
                  <button @click="verAsistencias(clase)" class="btn-tabla-ver-asistencia">
                    Ver asistencias
                  </button>
                </div>
                <!-- No se muestra nada para clases canceladas -->
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-state" style="margin-top: 24px;">
        No se encontraron clases para los filtros aplicados
      </p>
      </div>
    </div>

    <!-- Modal de Confirmación de Cancelación -->
    <div v-if="claseSeleccionada" class="modal-backdrop" role="dialog" aria-modal="true">
      <section class="confirm-modal">
        <h2>Cancelar clase</h2>
        <p>
          ¿Confirmás la cancelación de {{ claseSeleccionada.name }}? El turno se liberará en el calendario.
        </p>
        <div class="modal-actions">
          <button type="button" class="btn-secundario" @click="cerrarConfirmacionCancelacion">
            Volver
          </button>
          <button type="button" :disabled="cancelando" @click="ejecutarCancelacion">
            {{ cancelando ? 'Cancelando...' : 'Confirmar cancelación' }}
          </button>
        </div>
      </section>
    </div>

    <!-- Modal de Edición de Clase -->
    <div v-if="claseParaEditar" class="modal-backdrop" role="dialog" aria-modal="true">
      <section class="confirm-modal">
        <h2>Editar Clase</h2>
        <p>
          Editando: <strong>{{ claseParaEditar.actividad || claseParaEditar.name }}</strong> del <strong>{{ formatFecha(claseParaEditar.fecha_hora) }}</strong>
        </p>
        
        <div class="form-group-modal">
          <label for="edit-room">Salón</label>
          <select id="edit-room" v-model="formEdicion.room">
            <option>Sala 1</option>
            <option>Sala 2</option>
            <option>Sala 3</option>
          </select>
        </div>

        <div class="form-group-modal">
          <label for="edit-cupo">Cupos</label>
          <input id="edit-cupo" type="number" v-model.number="formEdicion.cupoMaximo" min="1" max="20" />
        </div>

        <div class="form-group-modal">
          <label for="edit-profesor">Profesor</label>
          <select id="edit-profesor" v-model="formEdicion.profesor_id">
            <option v-for="profesor in profesores" :key="profesor.id" :value="profesor.id">
              {{ profesor.nombre }} {{ profesor.apellido }}
            </option>
          </select>
        </div>

        <p v-if="editFeedbackMessage" :class="['feedback-message', editFeedbackType]" style="margin-top: 1rem;">
          {{ editFeedbackMessage }}
        </p>

        <div class="modal-actions">
          <button type="button" class="btn-secundario" @click="cerrarModalEdicion">
            Cancelar
          </button>
          <button type="button" :disabled="editando" @click="ejecutarEdicion">
            {{ editando ? 'Guardando...' : 'Confirmar edición' }}
          </button>
        </div>
      </section>
    </div>

    <!-- Modal de Lista de Asistencia -->
    <div v-if="claseParaAsistencia" class="modal-backdrop" role="dialog" aria-modal="true">
      <section class="confirm-modal">
        <h2>Lista de Asistencia</h2>
        <p>Clase: <strong>{{ claseParaAsistencia.actividad || claseParaAsistencia.name }}</strong> del <strong>{{ formatFecha(claseParaAsistencia.fecha_hora) }}</strong></p>

        <div v-if="cargandoAsistencia" class="loading-text">Cargando asistencias...</div>
        <div v-else-if="errorAsistencia" class="feedback-message error">{{ errorAsistencia }}</div>
        <div v-else-if="listaAsistencia.length === 0" class="empty-state" style="margin-top: 1rem;">No hubo inscriptos en esta clase.</div>
        
        <div v-else>
          <p class="asistencia-summary">
            Asistencias: {{ totalAsistencias }} / {{ listaAsistencia.length }}
          </p>
          <div class="tabla-responsiva-contenedor" style="margin-top: 16px; max-height: 300px; overflow-y: auto;">
            <table class="tabla-gestion-gym" aria-live="polite">
            <thead>
              <tr>
                <th>Alumno</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="asistente in listaAsistencia" :key="asistente.user_id">
                <td>{{ asistente.apellido }}, {{ asistente.username }}</td>
                <td>
                  <span :class="asistente.present ? 'etiqueta-estado-verde' : 'etiqueta-estado-roja'">
                    {{ asistente.present ? 'Asistió' : 'No asistió' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          </div>
        </div>

        <div class="modal-actions"><button type="button" class="btn-secundario" @click="cerrarAsistencias">Cerrar</button></div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.asistencia-summary {
  font-weight: bold;
  color: #572c57;
  background-color: #f6ea98;
  padding: 8px 12px;
  border-radius: 6px;
}

.acciones-columna {
  display: flex;
  gap: 8px;
}

.btn-tabla-asistencia {
  background-color: #9f5f91; /* Mismo color que editar/cancelar */
  color: #f6ea98;
  font-size: 13px;
}
/* Estilos unificados con la paleta de marca: #572c57, #9f5f91, #f5f5f5, #f6ea98, #e26972 */
.gestion-clases-container {
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 20px;
  color: #f5f5f5;
}

.titulo-principal {
  letter-spacing: 1px;
  margin: 0 0 6px 0;
  color: #f5f5f5;
}

.descripcion-panel {
  font-family: 'Bodoni Moda', serif;
  font-style: italic;
  color: #f6ea98;
  margin: 0 0 32px 0;
}

/* Tarjeta oscura contenedora (Idéntica a la de descuentos) */
.tarjeta-oscura-tabla {
  background-color: #572c57;
  border: 1px solid #9f5f91;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.subtitulo-seccion {
  color: #f5f5f5;
}

/* Estructura de Tabla Administrativa */
.tabla-encabezado {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 🌟 Botón Actualizar: Sin borde amarillo, ahora relleno con el violeta de la barra (#9f5f91) */
.btn-refrescar {
  font-size: 14px;
}

/* Filtros en cascada */
.filtros-contenedor {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  color: #f6ea98;
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 14px;
}

.form-group select {
  background-color: rgba(245, 245, 245, 0.1);
  border: 1px solid #9f5f91;
  border-radius: 8px;
  color: #f5f5f5;
  padding: 12px;
  font-size: 15px;
  outline: none;
}

.form-group select option {
  background-color: #572c57;
  color: #f5f5f5;
}

.form-group select:focus {
  border-color: #f6ea98;
}

.mt-4 {
  margin-top: 24px;
}

.tabla-responsiva-contenedor {
  overflow-x: auto;
}

.tabla-gestion-gym {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.tabla-gestion-gym th {
  background-color: #9f5f91;
  color: #f5f5f5;
  padding: 14px 12px;
  font-size: 14px;
  text-transform: uppercase;
  font-family: 'Anta', sans-serif;
}

/* 🌟 Forzamos a que las celdas hereden la fuente sans-serif limpia de los botones */
.tabla-gestion-gym td {
  padding: 14px 12px;
  border-bottom: 1px solid #9f5f91;
  font-family: sans-serif;
  font-size: 15px;
}

.fila-cancelada {
  background-color: rgba(0, 0, 0, 0.2);
  opacity: 0.6;
}

.col-actividad {
  font-family: sans-serif;
  font-weight: bold;
  color: #f6ea98;
}

.col-resaltada {
  font-weight: bold;
}

.texto-celda {
  color: #f5f5f5;
}

/* Badges de Estado */
.etiqueta-estado-verde {
  background-color: #319795;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  font-family: sans-serif;
}

.etiqueta-estado-roja {
  background-color: #e53e3e;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  font-family: sans-serif;
}

/* Botones de Cancelar en la Tabla */
.btn-tabla-cancelar {
  font-size: 13px;
  white-space: nowrap;
}

.btn-tabla-editar {
  background-color: #9f5f91; /* Color rojo, igual que el de cancelar */
  font-size: 13px;
  white-space: nowrap;
}

.btn-tabla-ver-asistencia {
  background-color: #9f5f91;
  font-size: 13px;
  white-space: nowrap;
}

.btn-tabla-cancelar:hover:not(:disabled) {
  transform: scale(1.02);
}

.btn-tabla-deshabilitado {
  cursor: not-allowed;
}

.loading-text, .empty-state {
  color: #b0a0c0;
  text-align: center;
  padding: 30px;
  font-family: sans-serif;
}

.empty-state {
  border: 1px dashed #9f5f91;
  border-radius: 6px;
}

.feedback-message {
  border-radius: 8px;
  font-family: sans-serif;
  margin: 0 0 16px;
  padding: 12px 14px;
}

.feedback-message.success {
  background: #d1fae5;
  color: #065f46;
}

.feedback-message.error {
  background: #fee2e2;
  color: #991b1b;
}

.modal-backdrop {
  align-items: center;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 20px;
  position: fixed;
  z-index: 1200;
}

.confirm-modal {
  background: #fff;
  border-radius: 8px;
  color: #4a3a4a;
  max-width: 420px;
  padding: 24px;
  width: 100%;
}

.confirm-modal h2 {
  color: #572c57;
  margin-top: 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.form-group-modal {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

.form-group-modal label {
  font-weight: bold;
  color: #572c57;
  margin-bottom: 0.5rem;
}

.form-group-modal input,
.form-group-modal select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
}

.btn-secundario {
  background: #f5f5f5;
  color: #572c57;
}
</style>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { CLASS_STATUS } from "../../constants/statuses";
import { getAllClasses, cancelarClaseCompleta, getClassAttendance, getProfesores, updateClass } from "../../services/api";
import { formatShortDate } from "../../utils/formatters";

const allClasses = ref([]);
const selectedStatus = ref("Todas");
const selectedMonth = ref(""); // e.g., "2024-07"
const selectedDay = ref(""); // e.g., 15
const selectedActivityName = ref(""); // e.g., "Yoga"


const cargando = ref(false);
const cancelando = ref(false);
const editando = ref(false);
const claseSeleccionada = ref(null);
const feedbackMessage = ref("");
const feedbackType = ref("success");

const editFeedbackMessage = ref("");
const editFeedbackType = ref("success");

const profesores = ref([]);
const claseParaEditar = ref(null);
const formEdicion = reactive({
  id: null,
  room: '',
  cupoMaximo: 20,
  profesor_id: null,
});

const claseParaAsistencia = ref(null);
const listaAsistencia = ref([]);
const cargandoAsistencia = ref(false);
const errorAsistencia = ref("");

const router = useRouter();

const totalAsistencias = computed(() => {
  return listaAsistencia.value.filter(a => a.present).length;
});

function isCancelled(clase) {
  return clase.estado === CLASS_STATUS.CANCELLED;
}

const availableMonths = computed(() => {
  const months = new Map();
  allClasses.value.forEach(c => {
    if (!c.fecha_hora) return;
    const d = new Date(c.fecha_hora);
    const yearMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    if (!months.has(yearMonth)) {
      const monthName = d.toLocaleString('es-AR', { month: 'long', year: 'numeric' });
      months.set(yearMonth, {
        value: yearMonth,
        label: monthName.charAt(0).toUpperCase() + monthName.slice(1)
      });
    }
  });
  return Array.from(months.values()).sort((a, b) => b.value.localeCompare(a.value)); // Descendente
});

const availableActivities = computed(() => {
  const activities = new Set();
  allClasses.value.forEach(c => {
    const activityName = c.actividad || c.name;
    if (activityName) {
      activities.add(activityName);
    }
  });
  return Array.from(activities).sort();
});

const displayedClasses = computed(() => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let classes = allClasses.value;

  // 1. Filter by Month
  if (selectedMonth.value) {
    classes = classes.filter(c => {
      if (!c.fecha_hora) return false;
      const d = new Date(c.fecha_hora);
      const yearMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      return yearMonth === selectedMonth.value;
    });
  }

  // 2. Filter by Day
  if (selectedDay.value) {
    classes = classes.filter(c => c.fecha_hora && new Date(c.fecha_hora).getDate() === Number(selectedDay.value));
  }

  // 3. Filter by Activity
  if (selectedActivityName.value) {
    classes = classes.filter(c => (c.actividad || c.name) === selectedActivityName.value);
  }
  
  // 4. Filter by Status
  if (selectedStatus.value !== 'Todas') {
    classes = classes.filter(c => getDisplayStatus(c) === selectedStatus.value);
  }

  // Ordenar por fecha descendente (más nuevas primero)
  return classes.sort((a, b) => new Date(b.fecha_hora) - new Date(a.fecha_hora));
});

// Watchers para resetear filtros en cascada
watch(selectedStatus, () => { /* No resetea otros filtros */ });
watch(selectedMonth, () => { selectedDay.value = ''; selectedActivityName.value = ''; });
watch(selectedDay, () => { selectedActivityName.value = ''; });


function goToAttendance(classId) {
  router.push(`/pasar-asistencia/${classId}`);
}

async function cargarClases() {
  cargando.value = true;
  feedbackMessage.value = "";
  try {
    const response = await getAllClasses();
    allClasses.value = response.data.classes || [];
  } catch (error) {
    feedbackType.value = "error";
    feedbackMessage.value = error.response?.data?.error || "No se pudieron cargar las clases.";
  } finally {
    cargando.value = false;
  }
}

async function cargarProfesores() {
  try {
    const response = await getProfesores();
    profesores.value = response.data.profesores || [];
  } catch (error) {
    feedbackType.value = "error";
    feedbackMessage.value = "No se pudieron cargar los profesores para la edición.";
    console.error("Error cargando profesores:", error);
  }
}

function abrirConfirmacionCancelacion(clase) {
  feedbackMessage.value = "";
  claseSeleccionada.value = clase;
}

function cerrarConfirmacionCancelacion() {
  claseSeleccionada.value = null;
}

function abrirModalEdicion(clase) {
  editFeedbackMessage.value = ""; // Limpiar mensaje de error al abrir
  editFeedbackType.value = "success";
  feedbackMessage.value = "";
  claseParaEditar.value = clase;
  formEdicion.id = clase.id;
  formEdicion.room = clase.room;
  formEdicion.cupoMaximo = clase.cupoMaximo;
  formEdicion.profesor_id = clase.profesor_id;
}

function cerrarModalEdicion() {
  claseParaEditar.value = null;
}


async function ejecutarCancelacion() {
  if (!claseSeleccionada.value) return;

  cancelando.value = true;
  try {
    const response = await cancelarClaseCompleta(claseSeleccionada.value.id);
    const claseAfectada = allClasses.value.find(c => c.id === claseSeleccionada.value.id);
    if (claseAfectada) {
      claseAfectada.estado = CLASS_STATUS.CANCELLED;
    }
    feedbackType.value = "success";
    feedbackMessage.value = response.data.message;
    cerrarConfirmacionCancelacion();
  } catch (error) {
    feedbackType.value = "error";
    feedbackMessage.value = error.response?.data?.error || "No se pudo procesar la cancelación.";
  } finally {
    cancelando.value = false;
  }
}

async function ejecutarEdicion() {
  if (!claseParaEditar.value) return;

  // Validación de cupos en el frontend
  if (formEdicion.cupoMaximo > 20) {
    editFeedbackType.value = "error";
    editFeedbackMessage.value = "El cupo máximo es de 20";
    return;
  }
  if (formEdicion.cupoMaximo < 1) {
    editFeedbackType.value = "error";
    editFeedbackMessage.value = "El cupo mínimo es 1";
    return;
  }

  // Validación de cupo contra inscriptos
  if (formEdicion.cupoMaximo < claseParaEditar.value.enrolled) {
    editFeedbackType.value = "error";
    editFeedbackMessage.value = "La cantidad de inscriptos supera el nuevo cupo ingresado";
    return;
  }

  // Validación de conflicto de salón en el frontend
  const claseOriginal = claseParaEditar.value;
  const salonConflictivo = allClasses.value.find(c =>
    c.id !== claseOriginal.id &&
    c.estado === 'Activa' &&
    c.fecha_hora === claseOriginal.fecha_hora &&
    c.room === formEdicion.room
  );

  if (salonConflictivo) {
    editFeedbackType.value = "error";
    editFeedbackMessage.value = `La '${formEdicion.room}' ya está ocupada por otra clase en ese horario`;
    return;
  }

  // Validación de conflicto de profesor en el frontend
  const profesorConflictivo = allClasses.value.find(c =>
    c.id !== claseOriginal.id &&
    c.estado === 'Activa' &&
    c.fecha_hora === claseOriginal.fecha_hora &&
    c.profesor_id === formEdicion.profesor_id
  );

  if (profesorConflictivo) {
    editFeedbackType.value = "error";
    editFeedbackMessage.value = "El profesor ya tiene una clase en ese día y horario";
    return;
  }

  editFeedbackMessage.value = ""; // Limpiar mensajes de error previos
  editando.value = true;
  try {
    const response = await updateClass(formEdicion.id, {
      room: formEdicion.room,
      cupoMaximo: formEdicion.cupoMaximo,
      profesor_id: formEdicion.profesor_id,
    });

    // Actualizar la clase en la lista local
    const index = allClasses.value.findIndex(c => c.id === formEdicion.id);
    if (index !== -1) {
      allClasses.value[index] = { ...allClasses.value[index], ...response.data.class };
    }

    feedbackType.value = "success";
    feedbackMessage.value = "Cambios realizados con éxito";
    cerrarModalEdicion();
  } catch (error) {
    editFeedbackType.value = "error";
    editFeedbackMessage.value = error.response?.data?.error || "No se pudo guardar la clase.";
  } finally {
    editando.value = false;
  }
}

async function verAsistencias(clase) {
  claseParaAsistencia.value = clase;
  cargandoAsistencia.value = true;
  errorAsistencia.value = "";
  listaAsistencia.value = [];

  try {
    const response = await getClassAttendance(clase.id);
    listaAsistencia.value = response.data.roster || [];
  } catch (error) {
    errorAsistencia.value = error.response?.data?.error || "No se pudo cargar la lista de asistencia.";
  } finally {
    cargandoAsistencia.value = false;
  }
}

function cerrarAsistencias() {
  claseParaAsistencia.value = null;
  listaAsistencia.value = [];
  errorAsistencia.value = "";
}

function getDisplayStatus(clase) {
  if (clase.estado === CLASS_STATUS.CANCELLED) {
    return 'Cancelada';
  }
  if (new Date(clase.fecha_hora) < new Date()) {
    return 'Finalizada';
  }
  return 'Activa';
}

function formatFecha(fechaIso) {
  return formatShortDate(fechaIso);
}

function formatDay(fechaIso) {
  if (!fechaIso) return 'N/A';
  const date = new Date(fechaIso);
  const weekday = date.toLocaleString('es-AR', { weekday: 'long' });
  return `${weekday.charAt(0).toUpperCase() + weekday.slice(1)} ${date.getDate()}`;
}

function formatMonth(fechaIso) {
  if (!fechaIso) return 'N/A';
  const date = new Date(fechaIso);
  const monthName = date.toLocaleString('es-AR', { month: 'long' });
  // Capitalizar la primera letra del mes
  return monthName.charAt(0).toUpperCase() + monthName.slice(1);
}

function formatTime(fechaIso) {
  if (!fechaIso) return 'N/A';
  const date = new Date(fechaIso);
  return date.toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit'
  }) + ' hs';
}

onMounted(() => {
  cargarClases();
  cargarProfesores();
});
</script>
