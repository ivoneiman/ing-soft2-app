<template>
  <div class="crear-clase-view">
    <h1>Crear Clase</h1>

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

      <div class="schedule-section">
        <p>Seleccione una fecha y horario</p>
        <Calendario @class-selected="handleClassSelected" />

        <div class="selection-summary" v-if="selectedDate || selectedSlot || selectedActivityName">
          <p v-if="selectedActivityName">
            <strong>Actividad seleccionada:</strong> {{ selectedActivityName }}
          </p>
          <p>
            <strong>Fecha seleccionada:</strong>
            <span>{{ selectedDateLabel || "No seleccionada" }}</span>
          </p>
          <p v-if="selectedSlot">
            <strong>Hora seleccionada:</strong> {{ selectedSlot }}
          </p>
        </div>
      </div>

      <button class="btn-primary" type="submit">Crear clase</button>

      <p class="message error" v-if="errorMessage">{{ errorMessage }}</p>
      <p class="message success" v-if="successMessage">{{ successMessage }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import Calendario from "@/components/calendario/calendario.vue";
import { getActivities, createClass } from "@/services/api.js";

const actividades = ref([]);
const form = reactive({
  activity_id: "",
  date: "",
  time: "",
});

const selectedDate = ref(null);
const selectedSlot = ref("");
const errorMessage = ref("");
const successMessage = ref("");

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

const loadActivities = async () => {
  try {
    const response = await getActivities();
    actividades.value = response.data || [];
  } catch (error) {
    console.error("Error cargando actividades:", error);
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
  form.date = selection.date ? selection.date.toISOString().split("T")[0] : "";
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
    });

    successMessage.value = "Clase creada correctamente.";
    form.activity_id = "";
    form.date = "";
    form.time = "";
    selectedDate.value = null;
    selectedSlot.value = "";
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
  color: #1f2937;
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

.selection-summary {
  padding: 1rem;
  border-radius: 0.75rem;
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