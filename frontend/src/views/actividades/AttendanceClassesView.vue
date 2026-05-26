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

      <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>
      <p v-if="loading" class="empty-state">Cargando clases...</p>
      <p v-else-if="attendanceClasses.length === 0" class="empty-state">
        No hay clases activas para tomar asistencia.
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

const today = new Date();
today.setHours(0, 0, 0, 0);

const todayLabel = computed(() => formatShortDate(today.toISOString()));

const attendanceClasses = computed(() =>
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
  .panel-header {
    align-items: stretch;
    flex-direction: column;
  }

  .refresh-button {
    width: 100%;
  }
}
</style>
