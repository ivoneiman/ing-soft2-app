<template>
  <div class="calendar-wrapper">
    <div class="calendar-header">
      <button type="button" class="nav-btn" @click="prevMonth" :disabled="loadingMonth">◀</button>
      <div class="month-year">
        {{ monthName }} {{ currentYear }}
      </div>
      <button type="button" class="nav-btn" @click="nextMonth" :disabled="loadingMonth">▶</button>
    </div>

    <div class="calendar-grid">
      <div class="weekday" v-for="day in ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']" :key="day">
        {{ day }}
      </div>

      <button
        v-for="day in calendarDays"
        :key="day.id"
        type="button"
        class="calendar-day"
        :class="{
          empty: day.empty,
          disabled: day.disabled,
          enabled: day.enabled,
          selected: day.selected,
        }"
        :disabled="day.disabled || day.empty"
        @click="selectDay(day)">
        {{ day.empty ? '' : day.date }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";

const props = defineProps({
  enabledDateKeys: {
    type: Array,
    default: undefined,
  },
});

const emit = defineEmits(["date-selected", "month-change"]);

const currentDate = ref(new Date());
const selectedDate = ref(null);
const loadingMonth = ref(false);

const currentYear = computed(() => currentDate.value.getFullYear());
const currentMonth = computed(() => currentDate.value.getMonth());

const monthName = computed(() => {
  const months = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
  ];
  return months[currentMonth.value];
});

function toDateKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

const calendarDays = computed(() => {
  const days = [];
  const firstDay = new Date(currentYear.value, currentMonth.value, 1);
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const enabledSet = props.enabledDateKeys ? new Set(props.enabledDateKeys) : null;

  // Días vacíos del mes anterior
  for (let i = 0; i < firstDay.getDay(); i++) {
    days.push({ id: `empty-${i}`, empty: true, date: null });
  }

  // Días del mes actual
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const date = new Date(currentYear.value, currentMonth.value, d);
    const dateKey = toDateKey(date);
    const isPast = date < today;
    const isEnabled = enabledSet ? enabledSet.has(dateKey) : true;
    const isSelected = selectedDate.value && toDateKey(selectedDate.value) === dateKey;

    days.push({
      id: `day-${dateKey}`,
      date: d,
      empty: false,
      disabled: isPast || !isEnabled,
      enabled: isEnabled && !isPast,
      selected: isSelected,
      dateObj: date,
    });
  }

  return days;
});

function prevMonth() {
  loadingMonth.value = true;
  currentDate.value = new Date(currentYear.value, currentMonth.value - 1, 1);
  emit("month-change", {
    year: currentDate.value.getFullYear(),
    month: currentDate.value.getMonth() + 1,
  });
  setTimeout(() => {
    loadingMonth.value = false;
  }, 50);
}

function nextMonth() {
  loadingMonth.value = true;
  currentDate.value = new Date(currentYear.value, currentMonth.value + 1, 1);
  emit("month-change", {
    year: currentDate.value.getFullYear(),
    month: currentDate.value.getMonth() + 1,
  });
  setTimeout(() => {
    loadingMonth.value = false;
  }, 50);
}

function selectDay(day) {
  if (!day.dateObj || day.disabled) return;
  selectedDate.value = day.dateObj;
  emit("date-selected", day.dateObj);
}

watch(
  () => props.enabledDateKeys,
  () => {
    // El computed calendarDays se actualiza automáticamente
  }
);
</script>

<style scoped>
.calendar-wrapper {
  max-width: 500px;
  padding: 1.75rem;
  border-radius: 16px;
  background: linear-gradient(135deg, #fff9e6 0%, #fef5cc 100%);
  border: 3px solid #f6ea98;
  box-shadow: 0 6px 20px rgba(246, 234, 152, 0.2);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f6ea98;
}

.month-year {
  font-size: 1.25rem;
  font-weight: 700;
  color: #8b7500;
  min-width: 150px;
  text-align: center;
  font-family: "Anton", sans-serif;
}

.nav-btn {
  font-size: 1.1rem;
  padding: 0.5rem 0.8rem;
  min-width: 40px;
}

.nav-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.6rem;
}

.weekday {
  text-align: center;
  font-weight: 700;
  color: #8b7500;
  padding: 0.6rem 0;
  font-size: 0.85rem;
  border-bottom: 2px solid #f6ea98;
  margin-bottom: 0.3rem;
}

.calendar-day {
  aspect-ratio: 1;
  font-size: 0.9rem;
  padding: 0;
}

.calendar-day.empty {
  border: none;
  background: transparent;
  cursor: default;
}

.calendar-day.enabled {
  cursor: pointer;
}

.calendar-day.enabled:hover {
  transform: scale(1.08);
  box-shadow: 0 2px 8px rgba(139, 117, 0, 0.15);
}

.calendar-day.selected {
  background: #f6ea98;
  color: #9f5f91;
  border-color: #f6ea98;
  font-weight: 700;
  box-shadow: 0 3px 10px rgba(139, 117, 0, 0.3);
}

.calendar-day.selected:hover {
  background: #efd87a;
  transform: scale(1.1);
}

.calendar-day:disabled {
  cursor: not-allowed;
}
</style>
