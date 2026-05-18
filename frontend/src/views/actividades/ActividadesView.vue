<template>
  <div class="catalog-view">
    <header class="catalog-header">
      <h1>Catálogo de clases</h1>
      <p class="lead">Elegí actividad, día y horario con cupo disponible.</p>
    </header>

    <div class="catalog-card">
      <!-- Paso 1: Actividad -->
      <section class="step">
        <h2 class="step-title"><span class="step-num">1</span> Actividad</h2>
        <div class="activity-grid">
          <button
            v-for="act in activities"
            :key="act.id"
            type="button"
            class="activity-btn"
            :class="{ active: selectedActivityId === act.id }"
            @click="selectActivity(act.id)">
            {{ act.name }}
          </button>
        </div>
      </section>

      <!-- Paso 2 y 3: Día y Horario en grid horizontal -->
      <div v-if="selectedActivityId" class="selection-grid">
        <!-- Columna izquierda: Calendario -->
        <section class="selection-col">
          <h2 class="step-title"><span class="step-num">2</span> Día</h2>
          <CatalogCalendario
            v-if="!loadingDays"
            :enabled-date-keys="calendarEnabledKeys"
            @date-selected="onDateSelected"
            @month-change="onMonthChange"
          />
          <div v-if="!loadingDays && enabledDateKeys.length === 0" class="info-box">
            No hay clases con cupo este mes para {{ selectedActivityName }}.
          </div>
        </section>

        <!-- Columna derecha: Horarios -->
        <section v-if="selectedDate" class="selection-col">
          <h2 class="step-title"><span class="step-num">3</span> Horario</h2>
          <div v-if="loadingSlots" class="info-box">Cargando horarios...</div>
          <template v-else>
            <div class="slots-grid">
              <button
                v-for="slot in availableSlots"
                :key="slot.id"
                type="button"
                class="slot-btn"
                :class="{ active: selectedClassId === slot.id }"
                @click="selectedClassId = slot.id">
                <div class="slot-time">{{ slot.time }}</div>
                <div class="slot-cupo">
                  {{ slot.available_spots }} {{ slot.available_spots === 1 ? 'cupo' : 'cupos' }}
                </div>
              </button>
            </div>

            <p v-if="!availableSlots.length" class="info-box">
              No hay horarios con cupo para este día.
            </p>

            <p v-if="fullCount > 0" class="waitlist-note">
              {{ fullCount }} horario{{ fullCount === 1 ? '' : 's' }} completo{{ fullCount === 1 ? '' : 's' }}.
            </p>
          </template>
        </section>
      </div>

      <!-- Resumen de selección -->
      <section v-if="selectedClass" class="summary">
        <h3>Tu selección</h3>
        <ul class="summary-list">
          <li><strong>Actividad:</strong> {{ selectedClass.actividad || selectedActivityName }}</li>
          <li><strong>Día:</strong> {{ selectedDateLabel }}</li>
          <li><strong>Horario:</strong> {{ selectedClass.time }} ({{ selectedClass.duration_minutes }} min)</li>
          <li><strong>Cupos libres:</strong> {{ selectedClass.available_spots }}</li>
        </ul>
        <button type="button" class="btn-inscribe" disabled title="Próximamente">
          Inscribirme (próximamente)
        </button>
      </section>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onBeforeUnmount } from "vue";
import CatalogCalendario from "@/components/calendario/CatalogCalendario.vue";
import { getActivities, getCatalogAvailability, getCatalogDays } from "../../services/api";

const DEFAULT_ACTIVITIES = [
  { id: 1, name: "Yoga" },
  { id: 2, name: "Funcional" },
  { id: 3, name: "Pilates" },
];

const activities = ref(DEFAULT_ACTIVITIES.slice());
const selectedActivityId = ref(null);
const selectedDate = ref(null);
const selectedClassId = ref("");
const availableSlots = ref([]);
const enabledDateKeys = ref([]);
const fullCount = ref(0);
const loadingDays = ref(false);
const loadingSlots = ref(false);
const error = ref("");

const selectedActivityName = computed(() => {
  const act = activities.value.find((a) => a.id === selectedActivityId.value);
  return act?.name || "";
});

const selectedDateLabel = computed(() => {
  if (!selectedDate.value) return "";
  return selectedDate.value.toLocaleDateString("es-ES", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
});

const selectedClass = computed(() =>
  availableSlots.value.find((s) => s.id === Number(selectedClassId.value)) || null
);

const calendarEnabledKeys = computed(() => {
  if (!selectedActivityId.value || loadingDays.value) return undefined;
  return enabledDateKeys.value;
});

function toDateKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

async function loadActivities() {
  try {
    const res = await getActivities();
    activities.value = res.data?.activities || res.data?.actividades || [];
    if (!activities.value.length) activities.value = DEFAULT_ACTIVITIES.slice();
  } catch {
    activities.value = DEFAULT_ACTIVITIES.slice();
  }
}

function selectActivity(id) {
  selectedActivityId.value = id;
  selectedDate.value = null;
  selectedClassId.value = "";
  availableSlots.value = [];
  fullCount.value = 0;
  enabledDateKeys.value = [];
  error.value = "";
  
  const now = new Date();
  loadMonthDays(now.getFullYear(), now.getMonth() + 1);
}

async function loadMonthDays(year, month) {
  if (!selectedActivityId.value) return;
  loadingDays.value = true;
  error.value = "";
  try {
    const res = await getCatalogDays(selectedActivityId.value, year, month);
    enabledDateKeys.value = res.data?.dates || [];
  } catch (err) {
    enabledDateKeys.value = [];
    error.value = err.response?.data?.error || "No se pudieron cargar los días disponibles.";
  } finally {
    loadingDays.value = false;
  }
}

function onMonthChange({ year, month }) {
  loadMonthDays(year, month);
}

async function onDateSelected(date) {
  selectedDate.value = date;
  selectedClassId.value = "";
  availableSlots.value = [];
  fullCount.value = 0;
  if (!date || !selectedActivityId.value) return;

  loadingSlots.value = true;
  error.value = "";
  try {
    const res = await getCatalogAvailability(selectedActivityId.value, toDateKey(date));
    availableSlots.value = res.data?.available || [];
    fullCount.value = res.data?.full_count || 0;
  } catch (err) {
    error.value = err.response?.data?.error || "No se pudieron cargar los horarios.";
  } finally {
    loadingSlots.value = false;
  }
}

onMounted(() => {
  loadActivities();
});

onActivated(() => {
  if (selectedActivityId.value) {
    const now = new Date();
    loadMonthDays(now.getFullYear(), now.getMonth() + 1);
  }
});

</script>

<style scoped>
.catalog-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  /* Sin background propio, usa el del body */
  min-height: calc(100vh - 140px);
}

.catalog-header h1 {
  font-family: "Anton", sans-serif;
  font-size: 2.5rem;
  color: #fff;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.lead {
  color: #e0c0e0;
  margin-bottom: 2rem;
  font-size: 1.05rem;
  font-weight: 500;
}

.catalog-card {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.step {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #e8dce8;
}

.step-title {
  font-family: "Anton", sans-serif;
  font-size: 1.3rem;
  color: #572c57;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.8rem;
  height: 1.8rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #9f5f91 0%, #572c57 100%);
  color: #fff;
  font-size: 0.95rem;
  font-weight: 700;
}

.activity-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.activity-btn {
  padding: 1rem 0.75rem;
  border: 2px solid #d0c0d0;
  border-radius: 14px;
  background: #fafaf8;
  color: #572c57;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: "Anton", sans-serif;
  font-size: 1.05rem;
  box-shadow: 0 2px 5px rgba(87, 44, 87, 0.05);
}

.activity-btn:hover {
  border-color: #9f5f91;
  background: #f5e6f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(87, 44, 87, 0.15);
}

.activity-btn.active {
  border-color: #572c57;
  background: linear-gradient(135deg, #9f5f91 0%, #572c57 100%);
  color: #fff;
  box-shadow: 0 4px 15px rgba(87, 44, 87, 0.25);
}

/* Grid horizontal para calendario y horarios */
.selection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.selection-col {
  min-width: 0;
}

/* Botones de horarios en grid */
.slots-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
}

.slot-btn {
  padding: 1rem;
  border: 2px solid #d0c0d0;
  border-radius: 12px;
  background: #fafaf8;
  color: #572c57;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.slot-btn:hover {
  border-color: #9f5f91;
  background: #f5e6f5;
  transform: translateY(-2px);
}

.slot-btn.active {
  border-color: #572c57;
  background: linear-gradient(135deg, #9f5f91 0%, #572c57 100%);
  color: #fff;
}

.slot-time {
  font-family: "Anton", sans-serif;
  font-size: 1.3rem;
  margin-bottom: 0.25rem;
}

.slot-cupo {
  font-size: 0.85rem;
  opacity: 0.9;
}

.info-box {
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 10px;
  color: #8a6a8a;
  font-size: 0.95rem;
  margin-top: 1rem;
  text-align: center;
}

.summary {
  margin-top: 2rem;
  padding: 1.75rem;
  border-radius: 16px;
  background: linear-gradient(135deg, #f5e6f5 0%, #ede5f5 100%);
  border: 2px solid #9f5f91;
  box-shadow: 0 4px 15px rgba(87, 44, 87, 0.1);
}

.summary h3 {
  font-family: "Anton", sans-serif;
  color: #572c57;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.summary-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  color: #4a3a4a;
  line-height: 1.8;
  font-weight: 500;
}

.summary-list li {
  padding: 0.4rem 0;
}

.summary-list strong {
  color: #572c57;
  font-weight: 700;
}

.btn-inscribe {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #9f5f91 0%, #572c57 100%);
  color: #fff;
  font-weight: 700;
  cursor: not-allowed;
  opacity: 0.65;
  font-size: 1.05rem;
  transition: all 0.3s ease;
}

.waitlist-note {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: #fff5f5;
  border-left: 4px solid #9f5f91;
  color: #572c57;
  font-size: 0.85rem;
}

.error {
  margin-top: 1rem;
  padding: 1rem;
  color: #b91c1c;
  background: #fee2e2;
  border-radius: 10px;
  border-left: 4px solid #b91c1c;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 900px) {
  .selection-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .activity-grid {
    grid-template-columns: 1fr;
  }
  
  .slots-grid {
    grid-template-columns: 1fr;
  }
}
</style>