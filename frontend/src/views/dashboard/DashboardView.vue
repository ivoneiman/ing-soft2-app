<template>
  <div class="gestion-clases-container">
    <h1 class="titulo-principal">MONITOREO Y CANCELACIÓN DE CLASES</h1>
    <p class="descripcion-panel">Panel de control exclusivo para la baja de turnos y asignación de créditos.</p>

    <div class="tarjeta-oscura-tabla">
      <div class="tabla-encabezado">
        <h2 class="subtitulo-seccion" style="margin: 0; border: none; padding: 0;">Clases Programadas en el Catálogo</h2>
        <button @click="cargarClases" class="btn-refrescar">Actualizar Lista</button>
      </div>

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
              :class="{ 'fila-cancelada': clase.estado === 'Cancelada' }"
            >
              <td class="col-actividad">{{ clase.name }}</td>
              <td class="texto-celda">{{ formatFecha(clase.fecha_hora) }}</td>
              <td class="col-resaltada texto-celda">{{ clase.time || 'No definido' }} hs</td>
              <td class="texto-celda">{{ clase.enrolled }} / {{ clase.cupoMaximo }}</td>
              <td>
                <span :class="clase.estado === 'Cancelada' ? 'etiqueta-estado-roja' : 'etiqueta-estado-verde'">
                  {{ clase.estado === 'Cancelada' ? 'Cancelada' : 'Activa' }}
                </span>
              </td>
              <td style="text-align: center;">
                <button 
                  @click="ejecutarCancelacion(clase.id, clase.name)"
                  :disabled="clase.estado === 'Cancelada'"
                  class="btn-tabla-cancelar"
                  :class="{ 'btn-tabla-deshabilitado': clase.estado === 'Cancelada' }"
                >
                  {{ clase.estado === 'Cancelada' ? 'Ya Cancelada' : 'Cancelar Clase' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
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
</style>

<script setup>
import { ref, onMounted } from "vue";
import { getAllClasses, cancelarClaseCompleta } from "../../services/api";

const clases = ref([]);
const cargando = ref(false);

async function cargarClases() {
  cargando.value = true;
  try {
    const response = await getAllClasses();
    let todasLasClases = response.data.classes || [];
    
    todasLasClases.sort((a, b) => {
      if (a.estado === 'Activa' && b.estado === 'Cancelada') return -1;
      if (a.estado === 'Cancelada' && b.estado === 'Activa') return 1;
      return 0;
    });
    
    clases.value = todasLasClases;
  } catch (error) {
    console.error("Error al cargar clases:", error);
  } finally {
    cargando.value = false;
  }
}

async function ejecutarCancelacion(claseId, nombreClase) {
  const seguro = confirm(`¿Estás seguro de cancelar la clase de ${nombreClase}? Se liberará el turno en el calendario.`);
  if (!seguro) return;

  try {
    const response = await cancelarClaseCompleta(claseId);
    alert(response.data.message);
    
    const claseAfectada = clases.value.find(c => c.id === claseId);
    if (claseAfectada) {
      claseAfectada.estado = "Cancelada";
    }
    
    clases.value.sort((a, b) => {
      if (a.estado === 'Activa' && b.estado === 'Cancelada') return -1;
      if (a.estado === 'Cancelada' && b.estado === 'Activa') return 1;
      return 0;
    });
  } catch (error) {
    const msg = error.message || "No se pudo procesar la cancelación.";
    alert(msg);
  }
}

function formatFecha(fechaIso) {
  if (!fechaIso) return "";
  const fecha = new Date(fechaIso);
  return fecha.toLocaleDateString("es-AR", { weekday: 'long', day: 'numeric', month: 'short' });
}

onMounted(() => {
  cargarClases();
});
</script>
