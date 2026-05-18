<template>
  <div class="calendar-layout">
    <div class="calendar-card">
      <div ref="calendarContainer" class="calendar-container"></div>
    </div>

    <div class="time-card" v-if="selectedDate">
      <h3>Horarios para {{ selectedDateLabel }}</h3>
      <select v-model="selectedSlot" class="slot-select" @change="onSlotSelected">
        <option disabled :value="null">Seleccione un horario</option>
        <option v-for="slot in filteredSlots" :key="slot" :value="slot">
          {{ slot }}
        </option>
      </select>
      
      <div v-if="filteredSlots.length === 0" class="empty">
        No hay horarios disponibles o están todos ocupados.
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, computed, defineEmits } from "vue";
import flatpickr from "flatpickr";
import { Spanish } from "flatpickr/dist/l10n/es.js";
import "flatpickr/dist/flatpickr.min.css";

const emit = defineEmits(["class-selected"]);
const props = defineProps({
  occupiedSlots: {
    type: Array,
    default: () => []
  }
});
const calendarContainer = ref(null);
const selectedDate = ref(null);
const selectedSlot = ref(null);
const availableSlots = ref([]);
let fpInstance = null;

const getAvailableSlots = (date) => {
  if (!date) return [];
  const weekday = date.getDay();
  if (weekday === 0) {
    return [];
 }
  return ["07:00","08:00","09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00","17:00", "18:00", "19:00", "20:00","21:00"];
};
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

const filteredSlots = computed(() => {
  return availableSlots.value.filter(slot => !props.occupiedSlots.includes(slot));
});

const onSlotSelected = () => {
  emit("class-selected", {
    date: selectedDate.value,
    slot: selectedSlot.value,
  });
};
const onDateChange = (selectedDates) => {
  if (selectedDates.length === 0) {
    selectedDate.value = null;
    availableSlots.value = [];
    selectedSlot.value = null;
    emit("class-selected", null);
    return;
  }
  selectedDate.value = selectedDates[0];
  selectedSlot.value = null;
  availableSlots.value = getAvailableSlots(selectedDate.value);
  emit("class-selected", {
    date: selectedDate.value,
    slot: null,
  });
};

onMounted(() => {
  fpInstance = flatpickr(calendarContainer.value, {
    locale: Spanish,
    dateFormat: "d/m/Y",
    inline: true,
    minDate: "today",
    onChange: onDateChange,
  });
});

onBeforeUnmount(() => {
  // Esto hace que si se cambia de pagina se saca la instancia del calendario
  if (fpInstance) {
    fpInstance.destroy();
  }
});
</script>

<style scoped>
.calendar-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.calendar-card {
  max-width: 420px;
  padding: 1.25rem;
  border: 1px solid transparent;
  border-radius: 0.75rem;
  background: transparent;
  flex: 1;
  min-width: 300px;
}

.calendar-container {
  margin-top: 0.75rem;
}

.time-card {
  flex: 1;
  min-width: 250px;
  padding: 1.5rem;
  background: transparent;
  border: none;
  border-radius: 0.75rem;
  margin-top: 1.25rem;
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

.empty,
.confirmation {
  margin-top: 1rem;
  color: #f5f5f5;
}
</style>

<style>
/* --- ESTILOS GLOBALES PARA FLATPICKR INLINE --- */

/* 1. Pintamos todas las capas de fondo principales */
.flatpickr-calendar, 
.flatpickr-innerContainer, 
.flatpickr-months,
.flatpickr-days,
.dayContainer,
.flatpickr-weekdays { /* <- Agregado la fila de los días de la semana */
  background-color: #f6ea98 !important;
  background: #f6ea98 !important; 
  border: none !important;        
}

/* 2. Cabecera del mes y contenedor del año */
.flatpickr-month,
.flatpickr-current-month {
  background-color: #f6ea98 !important;
  background: #f6ea98 !important;
}

.flatpickr-current-month .numInputWrapper input.cur-year:not(:hover),
.flatpickr-current-month .numInputWrapper input.cur-year:not(:focus) {
  color: #2c3e50 !important;
  opacity: 1 !important;
} /*este es el color de los numeros del año */

/* 1. El contenedor solo maneja el fondo transparente */
.flatpickr-current-month .numInputWrapper {
  background: transparent !important;
}

/* 2. El texto del año mantiene su color oscuro SIEMPRE */
.flatpickr-current-month .numInputWrapper input.cur-year,
.flatpickr-current-month .numInputWrapper input.cur-year[type="number"] {
  color: #2c3e50 !important;
  opacity: 1 !important;
  background: transparent !important;
}

/* 3. Forzamos el color del año cuando quitamos el mouse de encima */
.flatpickr-current-month .numInputWrapper input.cur-year:not(:hover),
.flatpickr-current-month .numInputWrapper input.cur-year:not(:focus) {
  color: #2c3e50 !important;
  opacity: 1 !important;
}/*este es el color de los numeros del año */

/* 3. Color del texto del Mes y Año (para que se lea en oscuro sobre el amarillo) */
.flatpickr-current-month .flatpickr-monthDropdown-months,
.flatpickr-current-month input.cur-year {
  color: #2c3e50 !important;
  font-weight: bold;
}

/* Flechas para cambiar de mes (por si quieres ajustar su color) */
.flatpickr-months .flatpickr-prev-month svg,
.flatpickr-months .flatpickr-next-month svg {
  fill: #2c3e50 !important;
}

/* 4. Color del texto de los días de la semana (Lu, Ma, Mi...) */
span.flatpickr-weekday {
  background: #f6ea98 !important;
  color: #2c3e50 !important;
  font-weight: 600;
}

/* 5. Color de los números activos */
.flatpickr-day {
  color: #2c3e50 !important; 
  background: transparent !important;
}

/* 6. Color de los números deshabilitados (pasados o fin de semana) */
.flatpickr-day.flatpickr-disabled,
.flatpickr-day.flatpickr-disabled:hover {
  color: #a0a0a0 !important; 
  background: transparent !important;
}

/* 7. El día seleccionado por el usuario */
.flatpickr-day.selected, 
.flatpickr-day.selected:hover {
  background: #4f46e5 !important; 
  color: white !important;
}
</style>