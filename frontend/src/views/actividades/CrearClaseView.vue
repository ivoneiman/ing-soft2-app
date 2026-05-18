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
        <label>Fecha y Horario</label>
        <!-- La key fuerza al componente a reiniciarse si cambia la actividad, limpiando su estado interno -->
        <Calendario @class-selected="handleClassSelected" :occupied-slots="occupiedSlotsForDate" :key="form.activity_id" />
      </div>

      <!-- PASO FINAL: Aparece solo cuando se ha seleccionado un horario -->
      <div class="final-step" v-if="form.time">
        <div class="selection-summary">
          <p><strong>Actividad:</strong> {{ selectedActivityName }}</p>
          <p><strong>Fecha:</strong> <span>{{ selectedDateLabel }}</span></p>
          <p><strong>Hora:</strong> {{ selectedSlot }}</p>
        </div>
        <button class="btn-primary" type="submit">Confirmar y Crear Clase</button>
      </div>

      <p class="message error" v-if="errorMessage">{{ errorMessage }}</p>
      <p class="message success" v-if="successMessage">{{ successMessage }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import Calendario from "@/components/calendario/Calendario.vue";
import { getActivities, createClass, getActivityClasses } from "@/services/api.js";

const actividades = ref([]);
const form = reactive({
  activity_id: "",
  date: "",
  time: "",
  cupoMaximo: 20,
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
});

const occupiedSlotsForDate = computed(() => {
  if (!form.date) return [];
  return occupiedClasses.value
    .filter(c => c.fecha_hora.startsWith(form.date))
    .map(c => c.time);
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

const handleClassSelected = (selection) => {
  if (!selection) return;
  selectedDate.value = selection.date;
  selectedSlot.value = selection.slot || "";
  
  if (selection.date) {
    const d = selection.date;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    form.date = `${year}-${month}-${day}`;
  } else {
    form.date = "";
  }
  
  form.time = selection.slot || "";
  errorMessage.value = "";
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
    await createClass({
      activity_id: Number(form.activity_id),
      date: form.date,
      time: form.time,
      cupoMaximo: form.cupoMaximo,
    });

    successMessage.value = "Clase creada correctamente.";
    // Limpiamos solo la hora para poder agregar otra clase en el mismo día rápidamente.
    // La actividad y la fecha se mantienen para que el usuario vea el horario desaparecer de la lista.
    form.time = "";
    selectedSlot.value = "";
    loadOccupiedClasses(); // Recargamos los horarios ocupados para la actividad actual
  } catch (error) {
    console.error("Error al crear clase:", error);
    errorMessage.value = error.response?.data?.error || "Error al crear la clase.";
  }
};
</script>

<style scoped>
.crear-clase-view {
  padding: 24px;
}

.crear-clase-form {
  max-width: 720px;
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
  margin-top: 1rem;
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
}

.message.success {
  color: #cbd5e1;
}
</style>