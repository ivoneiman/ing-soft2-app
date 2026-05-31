<template>
  <div class="catalog-view">
    <header class="catalog-header">
      <h1>Crear Nuevas Clases</h1>
      <p class="lead">Seleccioná actividad, día y horario. Se generarán clases para todos los días de ese mes.</p>
    </header>

    <div class="catalog-card">
      <!-- Paso 1: Actividad -->
      <section class="step">
        <h2 class="step-title"><span class="step-num">1</span> Actividad</h2>
        <div class="activity-grid">
          <button
            v-for="act in actividades"
            :key="act.id"
            type="button"
            class="activity-btn"
            :class="{ active: Number(form.activity_id) === act.id }"
            @click="selectActivity(act.id)">
            {{ act.name }}
          </button>
        </div>
        
        <!-- Aviso visible si el backend está apagado y falla la conexión -->
        <div v-if="actividades.length === 0 && errorMessage" class="error-connection mt-4">
          <p>⚠️ No se pudieron cargar las actividades.</p>
          <p class="small-text">Detalle: {{ errorMessage }}</p>
          <button type="button" @click="loadActivities" class="btn-retry">Reintentar conexión</button>
        </div>
      </section>

      <!-- Paso 2 y 3: Día y Horario -->
      <div v-if="form.activity_id" class="selection-grid">
        <section class="selection-col">
          <h2 class="step-title"><span class="step-num">2</span> Día</h2>
          <CatalogCalendario @date-selected="handleDateSelected" :key="form.activity_id" />
        </section>

        <section class="selection-col">
          <h2 class="step-title"><span class="step-num">3</span> Horario</h2>
          <div v-if="!selectedDate" class="info-box">
            Seleccioná un día en el calendario.
          </div>
          <template v-else>
            <div class="slots-grid">
              <button
                v-for="slot in availableSlots"
                :key="slot"
                type="button"
                class="slot-btn"
                :class="{ active: selectedSlot === slot }"
                @click="onSlotSelected(slot)">
                <div class="slot-time">{{ slot }}</div>
              </button>
            </div>
            <p v-if="availableSlots.length === 0" class="info-box">
              No hay horarios disponibles para todos los {{ getWeekdayName(selectedDate).toLowerCase() }} del mes.
            </p>
          </template>
        </section>
      </div>

      <!-- Resumen de creación -->
      <section v-if="selectedSlot" class="summary">
        <h3>Tu selección</h3>
        <ul class="summary-list">
          <li><strong>Actividad:</strong> {{ selectedActivityName }}</li>
          <li><strong>Días a crear:</strong> Todos los {{ getWeekdayName(selectedDate) }} del mes</li>
          <li><strong>Horario:</strong> {{ selectedSlot }}</li>
        </ul>
        <button type="button" class="btn-inscribe" @click="submitForm">
          Generar Clases del Mes
        </button>
      </section>

      <p v-if="successMessage" class="success">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import CatalogCalendario from "@/components/calendario/CatalogCalendario.vue";
import { getActivities, createClass, getActivityClasses } from "@/services/api.js";

const actividades = ref([]);
const form = reactive({
  activity_id: "",
  cupoMaximo: 20,
});

const selectedDate = ref(null);
const selectedSlot = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const occupiedClasses = ref([]);

const selectedActivityName = computed(() => {
  const actividad = actividades.value.find((item) => item.id === Number(form.activity_id));
  return actividad ? actividad.name : "";
});

const getWeekdayName = (date) => {
  if (!date) return "";
  const days = ["Domingos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábados"];
  return days[date.getDay()];
};

const loadOccupiedClasses = async () => {
  if (!form.activity_id) {
    occupiedClasses.value = [];
    return;
  }
  try {
    const response = await getActivityClasses(form.activity_id);
    occupiedClasses.value = response.data?.classes || [];
  } catch (error) {
    console.error("Error cargando clases ocupadas:", error);
    occupiedClasses.value = [];
  }
};

const selectActivity = (id) => {
  form.activity_id = id;
  loadOccupiedClasses();
  selectedDate.value = null;
  selectedSlot.value = "";
  successMessage.value = "";
  errorMessage.value = "";
};

// Calcula todas las fechas correspondientes a ese mismo día de la semana para el mes seleccionado
const targetDatesForSelectedDay = computed(() => {
  if (!selectedDate.value) return [];
  const selected = new Date(selectedDate.value);
  const month = selected.getMonth();
  const year = selected.getFullYear();
  const dayOfWeek = selected.getDay();

  const dates = [];
  let iterDate = new Date(year, month, 1);
  while (iterDate.getDay() !== dayOfWeek) {
    iterDate.setDate(iterDate.getDate() + 1);
  }
  while (iterDate.getMonth() === month) {
    const y = iterDate.getFullYear();
    const m = String(iterDate.getMonth() + 1).padStart(2, '0');
    const d = String(iterDate.getDate()).padStart(2, '0');
    dates.push(`${y}-${m}-${d}`);
    iterDate.setDate(iterDate.getDate() + 7);
  }
  return dates;
});

// Identifica qué horarios ya están ocupados en CUALQUIERA de esos días del mes
const occupiedSlotsForMonth = computed(() => {
  if (!selectedDate.value) return [];
  const targets = targetDatesForSelectedDay.value;
  const occupied = new Set();

  targets.forEach(fechaStr => {
    const classesForDate = occupiedClasses.value.filter(c => c.fecha_hora && c.fecha_hora.startsWith(fechaStr));
    classesForDate.forEach(c => occupied.add(c.time));
  });

  return Array.from(occupied);
});

const availableSlots = computed(() => {
  if (!selectedDate.value) return [];
  const weekday = selectedDate.value.getDay();
  if (weekday === 0) return []; // Domingos sin clase
  
  const allSlots = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"];
  const occupied = occupiedSlotsForMonth.value;
  
  const now = new Date();

  return allSlots.filter(slot => {
    if (occupied.includes(slot)) return false;
    
    // Verificar que al menos una de las clases que se van a generar con este horario sea en el futuro
    return targetDatesForSelectedDay.value.some(fechaStr => {
      const [year, month, day] = fechaStr.split('-');
      const [hour, minute] = slot.split(':');
      const slotDate = new Date(year, Number(month) - 1, day, hour, minute);
      return slotDate > now;
    });
  });
});

const loadActivities = async () => {
  errorMessage.value = "";
  try {
    const response = await getActivities();
    actividades.value = response.data || [];
  } catch (error) {
    console.error("Error cargando actividades:", error);
    errorMessage.value = error.message === "Network Error" ? "Servidor backend desconectado." : "Fallo de red.";
    actividades.value = [];
  }
};

onMounted(() => {
  loadActivities();
});

const handleDateSelected = (date) => {
  if (!date) return;
  
  // Ignorar clicks si el día es domingo (0)
  if (date.getDay() === 0) {
    errorMessage.value = "Los domingos el establecimiento se encuentra cerrado.";
    successMessage.value = "";
    selectedSlot.value = "";
    selectedDate.value = null;
    return;
  }

  selectedDate.value = date;
  selectedSlot.value = "";
  errorMessage.value = "";
  successMessage.value = "";
};

const onSlotSelected = (slot) => {
  selectedSlot.value = slot;
  successMessage.value = "";
  errorMessage.value = "";
};

const submitForm = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  const missing = [];
  if (!form.activity_id) missing.push("actividad");
  if (!selectedDate.value) missing.push("fecha");
  if (!selectedSlot.value) missing.push("hora");

  if (missing.length > 0) {
    errorMessage.value = `Por favor seleccione ${missing.join(", ")}.`;
    return;
  }

  try {
    const targetDates = targetDatesForSelectedDay.value;

    // Comprobar conflictos por si acaso antes de crear
    const conflicts = targetDates.filter(fechaStr =>
      occupiedClasses.value.some(c => c.fecha_hora && c.fecha_hora.startsWith(fechaStr) && c.time === selectedSlot.value)
    );

    if (conflicts.length > 0) {
      errorMessage.value = `Ya existen clases para la misma actividad en estas fechas: ${conflicts.join(', ')}.`;
      return;
    }

    const createdDates = [];
    for (const fechaStr of targetDates) {
      try {
        await createClass({
          activity_id: Number(form.activity_id),
          date: fechaStr,
          time: selectedSlot.value,
          cupoMaximo: form.cupoMaximo,
        });
        createdDates.push(fechaStr);
      } catch (err) {
        console.error("Fallo al crear la clase para la fecha:", fechaStr, err);
      }
    }

    successMessage.value = createdDates.length > 0 ? `Clases generadas con éxito para las fechas: ${createdDates.join(' | ')}.` : 'No se crearon clases.';
    selectedSlot.value = '';
    await loadOccupiedClasses();
  } catch (error) {
    errorMessage.value = error.response?.data?.error || "Error general al crear las clases.";
  }
};
</script>

<style scoped>
.catalog-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 140px);
}

.catalog-header h1 {
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
  transition: all 0.25s ease;
  box-shadow: 0 2px 5px rgba(87, 44, 87, 0.05);
}

.activity-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(87, 44, 87, 0.15);
}

.activity-btn.active {
  border-color: #f6ea98;
  background: #f6ea98;
  color: #9f5f91;
  box-shadow: 0 4px 15px rgba(87, 44, 87, 0.25);
}

.selection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.selection-col {
  min-width: 0;
}

.slots-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
}

.slot-btn {
  padding: 1rem;
  transition: all 0.2s ease;
  text-align: center;
}

.slot-btn:hover {
  transform: translateY(-2px);
}

.slot-btn.active {
  border-color: #f6ea98;
  background: #f6ea98;
  color: #9f5f91;
}

.slot-time {
  margin-bottom: 0.25rem;
  font-weight: bold;
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
  color: #572c57;
  margin-bottom: 1rem;
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
  transition: all 0.3s ease;
}

.mt-4 {
  margin-top: 1rem;
}

.error-connection {
  padding: 1rem;
  background-color: #fee2e2;
  border: 1px solid #b91c1c;
  border-radius: 10px;
  color: #b91c1c;
}

.error-connection .small-text {
  font-size: 0.85rem;
  opacity: 0.8;
  margin-top: 0.25rem;
}

.btn-retry {
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  background-color: #b91c1c;
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
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

.success {
  margin-top: 1rem;
  padding: 1rem;
  color: #027a48;
  background: #ecfdf3;
  border-radius: 10px;
  border-left: 4px solid #12b76a;
  font-weight: 700;
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
