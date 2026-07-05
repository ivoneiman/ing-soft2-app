<template>
  <div class="attendance-classes-view">
    <header class="page-header">
      <h1>Asistencias</h1>
      <p>Seleccioná la clase correcta antes de abrir el scanner.</p>
    </header>

    <section class="classes-panel">
      <div class="panel-header">
        <div>
          <h2>Clases disponibles</h2>
          <p>{{ todayLabel }}</p>
        </div>
        <button type="button" class="refresh-button" :disabled="loading" @click="loadClasses">
          {{ loading ? 'Actualizando...' : 'Actualizar' }}
        </button>
      </div>

      <section class="filters-panel">
        <div class="filter-grid">
          <label class="filter-field">
            <span>Tipo de actividad</span>
            <select v-model="selectedActivity">
              <option value="">Todas</option>
              <option v-for="activity in availableActivities" :key="activity" :value="activity">
                {{ activity }}
              </option>
            </select>
          </label>

          <label class="filter-field">
            <span>Día</span>
            <select v-model="selectedDay">
              <option value="">Todos</option>
              <option v-for="day in availableDays" :key="day" :value="day">
                {{ day }}
              </option>
            </select>
          </label>

          <label class="filter-field">
            <span>Horario</span>
            <select v-model="selectedTime">
              <option value="">Todos</option>
              <option v-for="time in availableTimes" :key="time" :value="time">
                {{ time }}
              </option>
            </select>
          </label>

          <label class="filter-field">
            <span>Salón</span>
            <select v-model="selectedRoom">
              <option value="">Todos</option>
              <option v-for="room in availableRooms" :key="room" :value="room">
                {{ room }}
              </option>
            </select>
          </label>
        </div>

        <div class="filters-actions">
          <button type="button" class="ghost-button" @click="resetFilters">
            Limpiar filtros
          </button>
          <p class="filters-summary">
            {{ attendanceClasses.length }} clase{{ attendanceClasses.length === 1 ? '' : 's' }} disponible{{ attendanceClasses.length === 1 ? '' : 's' }}
          </p>
        </div>
      </section>

      <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>
      <p v-if="loading" class="empty-state">Cargando clases...</p>
      <p v-else-if="attendanceClasses.length === 0" class="empty-state">
        No hay clases que coincidan con los filtros seleccionados.
      </p>

      <div v-else class="classes-grid">
        <article v-for="clase in attendanceClasses" :key="clase.id" class="class-card">
          <div>
            <span class="date-pill">{{ classDateLabel(clase.fecha_hora) }}</span>
            <h3>{{ clase.actividad || clase.name }}</h3>
            <dl>
              <div>
                <dt>Horario</dt>
                <dd>{{ clase.time || classTimeLabel(clase.fecha_hora) }} hs</dd>
              </div>
              <div>
                <dt>Inscriptos</dt>
                <dd>{{ clase.enrolled }} / {{ clase.cupoMaximo }}</dd>
              </div>
            </dl>
          </div>

          <button type="button" class="attendance-button" @click="startAttendance(clase.id)">
            Tomar asistencia
          </button>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { getAllClasses } from '@/services/api';
import { CLASS_STATUS } from '@/constants/statuses';
import { formatShortDate } from '@/utils/formatters';

const router = useRouter();
const classes = ref([]);
const loading = ref(false);
const errorMessage = ref('');
const selectedActivity = ref('');
const selectedDay = ref('');
const selectedTime = ref('');
const selectedRoom = ref('');

const today = new Date();
today.setHours(0, 0, 0, 0);

const todayLabel = computed(() => formatShortDate(today.toISOString()));

const weekdayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

function normalizeValue(value) {
  return String(value ?? '').trim().toLowerCase();
}

function getClassActivityName(clase) {
  return clase.actividad || clase.name || clase.activity_name || '';
}

function getClassDayLabel(clase) {
  if (!clase.fecha_hora) return '';
  return weekdayNames[new Date(clase.fecha_hora).getDay()];
}

function getClassTimeLabel(clase) {
  const explicitTime = clase.time || '';
  if (explicitTime) return explicitTime;

  if (!clase.fecha_hora) return '';

  return new Intl.DateTimeFormat('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(clase.fecha_hora));
}

function normalizeRoomName(room) {
  const value = String(room ?? '').trim();
  if (!value) return '';

  const normalized = value.toLowerCase();
  const match = normalized.match(/sala(?:n)?\s*([123])/i);
  if (match) {
    return `Salón ${match[1]}`;
  }

  return value;
}

function getClassRoom(clase) {
  return normalizeRoomName(clase.room || clase.salon || clase.location || '');
}

const baseAttendanceClasses = computed(() =>
  classes.value
    .filter((clase) => clase.estado === CLASS_STATUS.ACTIVE)
    .filter((clase) => {
      if (!clase.fecha_hora) return false;
      const classDate = new Date(clase.fecha_hora);
      classDate.setHours(0, 0, 0, 0);
      return classDate >= today;
    })
    .sort((a, b) => new Date(a.fecha_hora) - new Date(b.fecha_hora))
);

const attendanceClasses = computed(() =>
  baseAttendanceClasses.value.filter((clase) => {
    const matchesActivity = !selectedActivity.value || normalizeValue(getClassActivityName(clase)) === normalizeValue(selectedActivity.value);
    const matchesDay = !selectedDay.value || normalizeValue(getClassDayLabel(clase)) === normalizeValue(selectedDay.value);
    const matchesTime = !selectedTime.value || normalizeValue(getClassTimeLabel(clase)) === normalizeValue(selectedTime.value);
    const matchesRoom = !selectedRoom.value || normalizeValue(getClassRoom(clase)) === normalizeValue(selectedRoom.value);

    return matchesActivity && matchesDay && matchesTime && matchesRoom;
  })
);

const availableActivities = computed(() =>
  [...new Set(baseAttendanceClasses.value.map((clase) => getClassActivityName(clase)).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }))
);

const availableDays = computed(() =>
  [...new Set(baseAttendanceClasses.value.map((clase) => getClassDayLabel(clase)).filter(Boolean))]
    .sort((a, b) => weekdayNames.indexOf(a) - weekdayNames.indexOf(b))
);

const availableTimes = computed(() =>
  [...new Set(baseAttendanceClasses.value.map((clase) => getClassTimeLabel(clase)).filter(Boolean))]
    .sort()
);

const availableRooms = computed(() =>
  [...new Set(baseAttendanceClasses.value.map((clase) => getClassRoom(clase)).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }))
);

async function loadClasses() {
  loading.value = true;
  errorMessage.value = '';

  try {
    const response = await getAllClasses();
    classes.value = response.data.classes || [];
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'No se pudieron cargar las clases.';
  } finally {
    loading.value = false;
  }
}

function startAttendance(classId) {
  router.push({ name: 'ScanQr', params: { classId } });
}

function resetFilters() {
  selectedActivity.value = '';
  selectedDay.value = '';
  selectedTime.value = '';
  selectedRoom.value = '';
}

function classDateLabel(value) {
  if (!value) return '-';

  const classDate = new Date(value);
  const onlyDate = new Date(classDate);
  onlyDate.setHours(0, 0, 0, 0);

  if (onlyDate.getTime() === today.getTime()) return 'Hoy';

  return formatShortDate(value);
}

function classTimeLabel(value) {
  if (!value) return '-';

  return new Intl.DateTimeFormat('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

onMounted(loadClasses);
</script>

<style scoped>
.attendance-classes-view {
  color: #f5f5f5;
  margin: 40px auto;
  max-width: 1040px;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 28px;
}

.page-header h1,
.panel-header h2,
.class-card h3 {
  margin: 0;
}

.page-header p,
.panel-header p {
  color: #f6ea98;
  font-family: 'Bodoni Moda', serif;
  font-style: italic;
  margin: 6px 0 0;
}

.classes-panel {
  background-color: #572c57;
  border: 1px solid #9f5f91;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  padding: 24px;
}

.filters-panel {
  background: rgba(245, 245, 245, 0.08);
  border: 1px solid #9f5f91;
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 16px;
}

.filter-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-field span {
  color: #f6ea98;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
}

.filter-field select {
  background: #f5f5f5;
  border: 1px solid #9f5f91;
  border-radius: 6px;
  color: #2a142e;
  padding: 8px 10px;
}

.filters-actions {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-top: 12px;
}

.filters-summary {
  color: #d9cfe0;
  font-size: 0.95rem;
  margin: 0;
}

.ghost-button {
  background: transparent;
  border: 1px solid #f6ea98;
  color: #f6ea98;
  font-size: 13px;
  padding: 8px 12px;
}

.panel-header {
  align-items: center;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 20px;
}

.refresh-button,
.attendance-button {
  font-size: 14px;
  white-space: nowrap;
}

.classes-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.class-card {
  background: rgba(245, 245, 245, 0.08);
  border: 1px solid #9f5f91;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  justify-content: space-between;
  min-height: 220px;
  padding: 18px;
}

.date-pill {
  background: #f6ea98;
  border-radius: 999px;
  color: #572c57;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 14px;
  padding: 5px 10px;
}

.class-card h3 {
  color: #f5f5f5;
  font-size: 22px;
}

dl {
  display: grid;
  gap: 10px;
  margin: 18px 0 0;
}

dl div {
  align-items: baseline;
  display: flex;
  justify-content: space-between;
}

dt {
  color: #d9cfe0;
  font-size: 13px;
}

dd {
  color: #f5f5f5;
  font-weight: 700;
  margin: 0;
}

.attendance-button {
  width: 100%;
}

.empty-state,
.message {
  border-radius: 6px;
  font-family: sans-serif;
  margin: 0;
  padding: 18px;
  text-align: center;
}

.empty-state {
  border: 1px dashed #9f5f91;
  color: #d9cfe0;
}

.message.error {
  background: #fee2e2;
  color: #991b1b;
  margin-bottom: 16px;
}

@media (max-width: 620px) {
  .panel-header,
  .filters-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .refresh-button,
  .ghost-button {
    width: 100%;
  }
}
</style>
