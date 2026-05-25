<template>
  <div class="gestion-clases-container">
    <h1 class="titulo-principal">MONITOREO Y CANCELACIÓN DE CLASES</h1>
    <p class="descripcion-panel">Panel de control exclusivo para la baja de turnos y asignación de créditos.</p>

    <div class="tarjeta-oscura-tabla">
      <div class="tabla-encabezado">
        <h2 class="subtitulo-seccion" style="margin: 0; border: none; padding: 0;">Clases Programadas en el Catálogo</h2>
        <button @click="cargarClases" class="btn-refrescar">Actualizar lista</button>
      </div>

      <p v-if="feedbackMessage" :class="['feedback-message', feedbackType]">
        {{ feedbackMessage }}
      </p>

      <p v-if="cargando" class="loading-text">Cargando clases desde el servidor...</p>

      <p v-else-if="clases.length === 0" class="empty-state">
        No hay clases registradas en el catálogo actual.
      </p>

      <div v-else class="tabla-responsiva-contenedor">
        <table class="tabla-gestion-gym">
          <thead>
            <tr>
              <th>Actividad</th>
              <th>Fecha / Día</th>
              <th>Horario</th>
              <th>Cupos Ocupados</th>
              <th>Estado</th>
              <th style="text-align: center;">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="clase in clases" 
              :key="clase.id" 
              :class="{ 'fila-cancelada': isCancelled(clase) }"
            >
              <td class="col-actividad">{{ clase.name }}</td>
              <td class="texto-celda">{{ formatFecha(clase.fecha_hora) }}</td>
              <td class="col-resaltada texto-celda">{{ clase.time || 'No definido' }} hs</td>
              <td class="texto-celda">{{ clase.enrolled }} / {{ clase.cupoMaximo }}</td>
              <td>
                <span :class="isCancelled(clase) ? 'etiqueta-estado-roja' : 'etiqueta-estado-verde'">
                  {{ classStatusLabel(clase.estado) }}
                </span>
              </td>
              <td style="text-align: center;">
                <button 
                  @click="abrirConfirmacionCancelacion(clase)"
                  :disabled="isCancelled(clase)"
                  class="btn-tabla-cancelar"
                  :class="{ 'btn-tabla-deshabilitado': isCancelled(clase) }"
                >
                  {{ isCancelled(clase) ? 'Ya cancelada' : 'Cancelar clase' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

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
  </div>
</template>

<style scoped>
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

.btn-secundario {
  background: #f5f5f5;
  color: #572c57;
}
</style>

<script setup>
import { ref, onMounted } from "vue";
import { CLASS_STATUS, statusLabel } from "../../constants/statuses";
import { getAllClasses, cancelarClaseCompleta } from "../../services/api";
import { formatShortDate } from "../../utils/formatters";

const clases = ref([]);
const cargando = ref(false);
const cancelando = ref(false);
const claseSeleccionada = ref(null);
const feedbackMessage = ref("");
const feedbackType = ref("success");

function isCancelled(clase) {
  return clase.estado === CLASS_STATUS.CANCELLED;
}

function classStatusLabel(status) {
  return statusLabel("class", status || CLASS_STATUS.ACTIVE);
}

function ordenarClasesPorEstado(todasLasClases) {
  return [...todasLasClases].sort((a, b) => Number(isCancelled(a)) - Number(isCancelled(b)));
}

async function cargarClases() {
  cargando.value = true;
  feedbackMessage.value = "";
  try {
    const response = await getAllClasses();
    clases.value = ordenarClasesPorEstado(response.data.classes || []);
  } catch (error) {
    feedbackType.value = "error";
    feedbackMessage.value = error.response?.data?.error || "No se pudieron cargar las clases.";
  } finally {
    cargando.value = false;
  }
}

function abrirConfirmacionCancelacion(clase) {
  feedbackMessage.value = "";
  claseSeleccionada.value = clase;
}

function cerrarConfirmacionCancelacion() {
  claseSeleccionada.value = null;
}

async function ejecutarCancelacion() {
  if (!claseSeleccionada.value) return;

  cancelando.value = true;
  try {
    const response = await cancelarClaseCompleta(claseSeleccionada.value.id);
    const claseAfectada = clases.value.find(c => c.id === claseSeleccionada.value.id);
    if (claseAfectada) {
      claseAfectada.estado = CLASS_STATUS.CANCELLED;
    }
    clases.value = ordenarClasesPorEstado(clases.value);
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

function formatFecha(fechaIso) {
  return formatShortDate(fechaIso);
}

onMounted(() => {
  cargarClases();
});
</script>
