<template>
  <div class="crear-clase-view">
    <h1>Crear Nueva Clase</h1>

    <form class="crear-clase-form" @submit.prevent="submitForm">
      <label>
        Actividad
        <select v-model="form.activity_id">
          <option disabled value="">Seleccione una actividad</option>
          <option v-for="actividad in actividades" :key="actividad.id" :value="actividad.id">
            {{ actividad.name }}
          </option>
        </select>
      </label>

      <!-- Aviso visible si el backend está apagado y falla la conexión -->
      <div v-if="actividades.length === 0 && errorMessage" class="error-connection">
        <p>⚠️ No se pudieron cargar las actividades.</p>
        <p class="small-text">Detalle: {{ errorMessage }}</p>
        <button type="button" @click="loadActivities" class="btn-retry">Reintentar conexión</button>
      </div>

      <!-- PASO 2: Aparece solo cuando se ha seleccionado una actividad -->
      <div class="schedule-section" v-if="form.activity_id">
        <label>
          Tipo de creación
          <select v-model="form.tipo">
            <option value="individual">Clase sola</option>
            <option value="mensual">Clase mensual</option>
          </select>
        </label>
        <label>Fecha y Horario</label>
        
        <div class="calendar-layout">
          <CatalogCalendario @date-selected="handleDateSelected" :key="form.activity_id" />
          
          <!-- Panel derecho: Horarios y botón de confirmación -->
          <div class="right-panel">
            <div class="time-card" v-if="selectedDate">
              <h3>Horarios disponibles para {{ selectedDateLabel }}</h3>
              <select v-model="form.time" class="slot-select" @change="onSlotSelected">
                <option disabled value="">Seleccione un horario</option>
                <option v-for="slot in availableSlots" :key="slot" :value="slot">
                  {{ slot }}
                </option>
              </select>
              
              <div v-if="availableSlots.length === 0" class="empty">
                No hay horarios disponibles para el día de la fecha.
              </div>
            </div>

            <!-- PASO FINAL: Movido aquí para que quede a la derecha del calendario -->
            <div class="final-step" v-if="form.time">
              <div class="selection-summary">
                <p><strong>Actividad:</strong> {{ selectedActivityName }}</p>
                <p><strong>Fecha:</strong> <span>{{ selectedDateLabel }}</span></p>
                <p><strong>Tipo de creacion:</strong> {{ form.tipo === 'mensual' ? 'Mensual (repetirá el mismo día y hora en el mes)' : 'Individual' }}</p>
                <p><strong>Hora:</strong> {{ selectedSlot }}</p>
              </div>
              <button class="btn-primary" type="submit">Crear Clase</button>
            </div>

            <!-- Mensajes movidos al panel derecho para que reemplacen al botón cuando desaparece -->
            <p class="message error" v-if="errorMessage">{{ errorMessage }}</p>
            <p class="message success" v-if="successMessage">{{ successMessage }}</p>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import CatalogCalendario from "@/components/calendario/CatalogCalendario.vue";
import { getActivities, createClass, getActivityClasses } from "@/services/api.js";

const actividades = ref([]);
const form = reactive({
  activity_id: "",
  date: "",
  time: "",
  cupoMaximo: 20,
  tipo: 'individual',
});

const selectedDate = ref(null);
const selectedSlot = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const occupiedClasses = ref([]);

const selectedDateLabel = computed(() => {
  return selectedDate.value
    ? selectedDate.value.toLocaleDateString("es-ES", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "";
});

const selectedActivityName = computed(() => {
  const actividad = actividades.value.find((item) => item.id === Number(form.activity_id));
  return actividad ? actividad.name : "";
});

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

watch(() => form.activity_id, () => {
  // Al cambiar de actividad, reseteamos la selección de fecha y hora para evitar inconsistencias
  loadOccupiedClasses();
  form.date = "";
  form.time = "";
  selectedDate.value = null;
  selectedSlot.value = "";
  successMessage.value = "";
  errorMessage.value = "";
});

const occupiedSlotsForDate = computed(() => {
  if (!form.date) return [];
  return occupiedClasses.value
    .filter(c => c.fecha_hora.startsWith(form.date))
    .map(c => c.time);
});

const availableSlots = computed(() => {
  if (!selectedDate.value) return [];
  const weekday = selectedDate.value.getDay();
  if (weekday === 0) return []; // Domingos sin clase
  
  const allSlots = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"];
  const occupied = occupiedSlotsForDate.value;
  
  return allSlots.filter(slot => !occupied.includes(slot));
});

const loadActivities = async () => {
  errorMessage.value = ""; // Limpiamos errores previos
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
    form.time = "";
    form.date = "";
    selectedSlot.value = "";
    selectedDate.value = null;
    return;
  }

  selectedDate.value = date;
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  form.date = `${year}-${month}-${day}`;
  
  // Reseteamos el horario al cambiar de día
  form.time = "";
  selectedSlot.value = "";
  errorMessage.value = "";
  successMessage.value = "";
};

const onSlotSelected = () => {
  selectedSlot.value = form.time;
  successMessage.value = "";
};

const submitForm = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  const missing = [];
  if (!form.activity_id) missing.push("actividad");
  if (!form.date) missing.push("fecha");
  if (!form.time) missing.push("hora");

  if (missing.length > 0) {
    errorMessage.value = `Por favor seleccione ${missing.join(" y ")}.`;
    return;
  }

  try {
    if (form.tipo === 'individual') {
      await createClass({
        activity_id: Number(form.activity_id),
        date: form.date,
        time: form.time,
        cupoMaximo: form.cupoMaximo,
        tipo: form.tipo,
      });

      successMessage.value = "Clase creada exitosamente.";
      form.time = "";
      selectedSlot.value = "";
      await loadOccupiedClasses();
      return;
    }

    // Si es mensual: primero calcular todas las fechas objetivo (mismo día de la semana)
    const startDate = new Date(selectedDate.value);
    const month = startDate.getMonth();
    const targetDates = [];
    let iterDate = new Date(startDate);

    while (iterDate.getMonth() === month) {
      const y = iterDate.getFullYear();
      const m = String(iterDate.getMonth() + 1).padStart(2, '0');
      const d = String(iterDate.getDate()).padStart(2, '0');
      const fechaStr = `${y}-${m}-${d}`;
      targetDates.push(fechaStr);
      iterDate.setDate(iterDate.getDate() + 7);
    }

    // Comprobar conflictos antes de crear: si alguna fecha ya tiene clase en ese horario, bloquear toda la operación
    const conflicts = targetDates.filter(fechaStr =>
      occupiedClasses.value.some(c => c.fecha_hora && c.fecha_hora.startsWith(fechaStr) && c.time === form.time)
    );

    if (conflicts.length > 0) {
      errorMessage.value = `No se puede crear la clase de manera mensual porque ya existen clases para la misma actividad en estas fechas: ${conflicts.join(', ')}.`;
      return;
    }

    // No hay conflictos: crear todas las fechas
    const createdDates = [];
    for (const fechaStr of targetDates) {
      try {
        await createClass({
          activity_id: Number(form.activity_id),
          date: fechaStr,
          time: form.time,
          cupoMaximo: form.cupoMaximo,
          tipo: form.tipo,
        });
        createdDates.push(fechaStr);
      } catch (err) {
        // Si hay error creando alguna fecha, reportarlo y continuar
      }
    }

    successMessage.value = createdDates.length > 0 ? `Clases creadas: ${createdDates.join(', ')}.` : 'No se crearon clases.';
    form.time = '';
    selectedSlot.value = '';
    await loadOccupiedClasses();
  } catch (error) {
    console.error("Error al crear clase:", error);
    errorMessage.value = error.response?.data?.error || "Error al crear la clase.";
  }
};
</script>

<style scoped>
.crear-clase-view {
  padding: 8px 24px 24px 24px; /* Reducido el padding superior para subir toda la vista un poco */
  max-width: 900px;
  margin: 0 auto; /* Centra todo el bloque en la pantalla equilibrando los márgenes */
}

.crear-clase-view h1 {
  text-align: center; /* Centra el título para que acompañe el diseño */
  margin-bottom: 1.5rem;
}

.crear-clase-form {
  width: 100%;
  display: grid;
  gap: 1.25rem;
}

.crear-clase-form label {
  display: grid;
  gap: 0.5rem;
  font-weight: 600;
  color: #f5f5f5;
}

.crear-clase-form input,
.crear-clase-form textarea,
.crear-clase-form select {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.75rem;
  background: #ffffff;
  color: #0f172a;
}

.crear-clase-form textarea {
  min-height: 120px;
  resize: vertical;
}

.help-text {
  margin: 0;
  color: #6b7280;
  font-size: 0.95rem;
}

.schedule-section {
  display: grid;
  gap: 1rem;
}

.calendar-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.right-panel {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.time-card {
  padding: 1.5rem;
  background: transparent;
  border: none;
  border-radius: 0.75rem;
  color: #f5f5f5;
}

.slot-select {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 0.75rem;
  background: #ffffff;
  color: #0f172a;
  cursor: pointer;
  padding: 0.85rem 1rem;
  font-size: 1rem;
  margin-top: 1rem;
}

.empty {
  margin-top: 1rem;
  color: #f5f5f5;
}

.error-connection {
  padding: 1rem;
  background-color: rgba(185, 28, 28, 0.2);
  border: 1px solid #b91c1c;
  border-radius: 0.75rem;
  color: #fca5a5;
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

.selection-summary {
  padding: 1rem;
  border-radius: 0.75rem;
  color: #f5f5f5;
}

.selection-summary p {
  color: #f5f5f5;
  line-height: 1.5;
}

.selection-summary strong {
  color: #f6ea98;
}

.final-step {
  padding: 1.5rem;
  border-radius: 0.75rem;
  background-color: rgba(0, 0, 0, 0.1);
  display: grid;
  gap: 1rem;
}

.btn-primary {
  width: fit-content;
  padding: 0.95rem 1.5rem;
  border: none;
  border-radius: 9999px;
  background: #4f46e5;
  color: white;
  cursor: pointer;
  font-weight: 700;
}

.btn-primary:hover {
  background: #4338ca;
}

.message {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.4;
}

.message.error {
  color: #b91c1c;
  background-color: #ffffff;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 1.05rem;
  font-weight: 600;
  width: fit-content; /* Hace que el fondo blanco abarque solo el texto */
}

.message.success {
  color: #4ade80; /* Un verde más vibrante */
  font-size: 1.15rem; /* Letra más grande para destacar */
  font-weight: 600;
  background-color: rgba(74, 222, 128, 0.1); /* Fondo sutil verde */
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(74, 222, 128, 0.3);
  text-align: center;
}
</style>