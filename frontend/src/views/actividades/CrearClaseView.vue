<template>
  <div class="catalog-view">
    <header class="catalog-header">
      <h1>Crear Nuevas Clases</h1>
      <p class="lead">Seleccioná actividad, día y horario para generar las clases de todo el mes.</p>
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
          <div class="day-grid">
            <button
              v-for="day in weekDays"
              :key="day.value"
              type="button"
              class="day-btn"
              :class="{ active: selectedDayOfWeek === day.value }"
              @click="handleDaySelected(day.value)">
              {{ day.name }}
            </button>
          </div>
        </section>

        <section class="selection-col">
          <h2 class="step-title"><span class="step-num">3</span> Horario</h2>
          <div v-if="selectedDayOfWeek === null" class="info-box">
            Seleccioná un día de la semana.
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
              No hay horarios disponibles para los {{ getWeekdayName(selectedDayOfWeek).toLowerCase() }} de este mes.
            </p>
          </template>
        </section>

        <!-- Paso 4: Salón -->
        <section v-if="selectedSlot" class="selection-col" style="grid-column: 1 / -1;">
          <h2 class="step-title"><span class="step-num">4</span> Salón</h2>
          <div class="slots-grid" style="grid-template-columns: repeat(3, 1fr);">
            <button
              v-for="room in ROOM_OPTIONS"
              :key="room"
              type="button"
              class="slot-btn"
              :class="{ active: selectedRoom === room }"
              :disabled="!isRoomAvailable(room)"
              @click="onRoomSelected(room)">
              <div class="slot-time">{{ room }}</div>
              <div style="font-size: 0.8rem; font-weight: normal; margin-top: 4px;" v-if="!isRoomAvailable(room)">(Ocupado)</div>
            </button>
          </div>
        </section>

        <!-- Paso 5: Profesor -->
        <section v-if="selectedRoom" class="selection-col" style="grid-column: 1 / -1;">
          <h2 class="step-title"><span class="step-num">5</span> Profesor</h2>
          <select v-model="form.profesor_id" class="profesor-select">
            <option :value="null" disabled>Seleccione un profesor</option>
            <option
              v-for="profesor in profesoresDeLaActividad"
              :key="profesor.id"
              :value="profesor.id"
              :disabled="!isProfesorAvailable(profesor.id)"
            >
              {{ profesor.nombre }} {{ profesor.apellido }} {{ !isProfesorAvailable(profesor.id) ? '(Ocupado)' : '' }}
            </option>
          </select>
          <p v-if="profesoresDisponiblesDeLaActividad.length === 0" class="info-box">
            No hay profesores cargados para {{ selectedActivityName }} en el horario seleccionado.
          </p>
        </section>

        <!-- Paso 6: Cupos -->
        <section v-if="form.profesor_id" class="selection-col" style="grid-column: 1 / -1;">
          <h2 class="step-title"><span class="step-num">6</span> Cupos de la clase</h2>
            <input
              type="number"
              v-model.number="form.cupoMaximo"
              class="profesor-select"
              placeholder="Ej: 15"
            />
            <small class="input-hint">La capacidad debe estar entre 1 y 20.</small>
        </section>

      </div>

      <!-- Resumen de creación -->
      <section v-if="form.profesor_id" class="summary">
        <h3>Tu selección</h3>
        <ul class="summary-list">
          <li><strong>Actividad:</strong> {{ selectedActivityName }}</li>
          <li><strong>Salón:</strong> {{ selectedRoom }}</li>
          <li><strong>Días a crear:</strong> Todos los {{ getWeekdayName(selectedDayOfWeek).toLowerCase() }} de los próximos 3 meses</li>
          <li><strong>Profesor:</strong> {{ selectedProfesorName || 'Sin asignar' }}</li>
          <li><strong>Horario:</strong> {{ selectedSlot }}</li>
          <li><strong>Cupos por clase:</strong> {{ form.cupoMaximo }}</li>
        </ul>
        <div style="text-align: center; margin-top: 1rem;">
          <button type="button" class="btn-inscribe" @click="submitForm">
            Generar Clases del Mes
          </button>
        </div>
      </section>

      <p v-if="successMessage" class="success">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { getActivities, createClass, getActivityClasses } from "@/services/api.js";
import axios from "axios";

const actividades = ref([]);
const form = reactive({
  activity_id: "",
  cupoMaximo: 20,
  profesor_id: null,
});

const ROOM_OPTIONS = ["Sala 1", "Sala 2", "Sala 3"];

const selectedDayOfWeek = ref(null);
const selectedSlot = ref("");
const selectedRoom = ref("");
const errorMessage = ref("");
const profesores = ref([]);
const successMessage = ref("");
const occupiedClasses = ref([]);
const weekDays = [
  { name: 'Lunes', value: 1 }, { name: 'Martes', value: 2 }, { name: 'Miércoles', value: 3 },
  { name: 'Jueves', value: 4 }, { name: 'Viernes', value: 5 }, { name: 'Sábado', value: 6 }
];



const selectedActivityName = computed(() => {
  const actividad = actividades.value.find((item) => item.id === Number(form.activity_id));
  return actividad ? actividad.name : "";
});

const selectedProfesorName = computed(() => {
  const profesor = profesores.value.find(p => p.id === form.profesor_id);
  return profesor ? `${profesor.nombre} ${profesor.apellido}` : null;
});

const profesoresDeLaActividad = computed(() => {
  if (!form.activity_id) return [];
  const activityId = Number(form.activity_id);
  return profesores.value.filter(p => (p.actividades || []).some(a => a.id === activityId));
});

const profesoresDisponiblesDeLaActividad = computed(() => {
  return profesoresDeLaActividad.value.filter(p => isProfesorAvailable(p.id));
});

const getWeekdayName = (dayIndex) => {
  if (dayIndex === null) return "";
  const days = ["Domingos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábados"];
  return days[dayIndex];
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
  form.profesor_id = null;
  loadOccupiedClasses();
  selectedDayOfWeek.value = null;
  selectedSlot.value = "";
  selectedRoom.value = "";
  successMessage.value = "";
  errorMessage.value = "";
};

// Calcula todas las fechas correspondientes a ese mismo día de la semana para el mes seleccionado
const targetDatesForSelectedDay = computed(() => {
  if (selectedDayOfWeek.value === null) return [];
  
  const now = new Date();
  const dayOfWeek = selectedDayOfWeek.value;
  const selectedHour = selectedSlot.value ? parseInt(selectedSlot.value.split(':')[0], 10) : 23;
  const selectedMinute = selectedSlot.value ? parseInt(selectedSlot.value.split(':')[1], 10) : 59;

  const dates = [];
  // Empezamos a buscar desde hoy
  let iterDate = new Date(now);

  // Avanzamos hasta encontrar el próximo día de la semana seleccionado (o hoy si coincide)
  while (iterDate.getDay() !== dayOfWeek) {
    iterDate.setDate(iterDate.getDate() + 1);
  }

  // Si el día encontrado es hoy y la hora seleccionada ya pasó, empezamos desde la próxima semana
  if (iterDate.getFullYear() === now.getFullYear() &&
      iterDate.getMonth() === now.getMonth() &&
      iterDate.getDate() === now.getDate()) {
    if (selectedHour < now.getHours() || (selectedHour === now.getHours() && selectedMinute <= now.getMinutes())) {
      iterDate.setDate(iterDate.getDate() + 7);
    }
  }

  // Recorremos los próximos 3 meses
  const threeMonthsFromNow = new Date(now.getFullYear(), now.getMonth() + 3, now.getDate());
  while (iterDate <= threeMonthsFromNow) {
    const y = iterDate.getFullYear();
    const m = String(iterDate.getMonth() + 1).padStart(2, '0');
    const d = String(iterDate.getDate()).padStart(2, '0');
    dates.push(`${y}-${m}-${d}`);
    iterDate.setDate(iterDate.getDate() + 7);
  }
  return dates;
});

// Identifica qué horarios ya están 100% ocupados (los 3 salones tomados por otras clases,
// sin importar la actividad). La misma actividad puede repetirse en un horario si queda
// al menos un salón libre.
const occupiedSlotsForMonth = computed(() => {
  if (selectedDayOfWeek.value === null) return [];
  const targets = targetDatesForSelectedDay.value;
  const completelyOccupiedSlots = new Set();
  const allSlots = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"];

  allSlots.forEach(slot => {
     const usedRooms = new Set();

     targets.forEach(fechaStr => {
        const classesAtSlot = occupiedClasses.value.filter(c =>
          c.fecha_hora && c.fecha_hora.startsWith(fechaStr) && c.time === slot
        );

        classesAtSlot.forEach(c => {
           if (c.room) usedRooms.add(c.room);
        });
     });

     if (usedRooms.size >= 3) {
        completelyOccupiedSlots.add(slot);
     }
  });

  return Array.from(completelyOccupiedSlots);
});

const availableSlots = computed(() => {
  if (selectedDayOfWeek.value === null) return [];
  
  const allSlots = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"];
  const occupied = occupiedSlotsForMonth.value;
  
  const now = new Date();

  return allSlots.filter(slot => {
    if (occupied.includes(slot)) return false;
    
    const [hour, minute] = slot.split(':').map(Number);

    // Verificar que al menos una de las clases que se van a generar con este horario sea en el futuro
    return targetDatesForSelectedDay.value.some(fechaStr => {
      const [year, month, day] = fechaStr.split('-');
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

const loadProfesores = async () => {
  try {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    const response = await axios.get(`${baseURL}/profesores`, { withCredentials: true });
    profesores.value = response.data.profesores || [];
  } catch (error) {
    console.error("Error cargando profesores:", error);
    profesores.value = [];
  }
};

onMounted(() => {
  loadActivities();
  loadProfesores();
});

const handleDaySelected = (dayOfWeek) => {
  selectedDayOfWeek.value = dayOfWeek;
  selectedSlot.value = "";
  selectedRoom.value = "";
  errorMessage.value = "";
  successMessage.value = "";
};

const onSlotSelected = (slot) => {
  selectedSlot.value = slot;
  selectedRoom.value = "";
  successMessage.value = "";
  errorMessage.value = "";
};

const isRoomAvailable = (room) => {
  if (selectedDayOfWeek.value === null || !selectedSlot.value) return false;
  const targets = targetDatesForSelectedDay.value;

  return !occupiedClasses.value.some(c =>
    c.fecha_hora &&
    targets.some(t => c.fecha_hora.startsWith(t)) &&
    c.time === selectedSlot.value &&
    c.room === room
  );
};

const onRoomSelected = (room) => {
  selectedRoom.value = room;
  successMessage.value = "";
  errorMessage.value = "";
};

const isProfesorAvailable = (profesorId) => {
  if (selectedDayOfWeek.value === null || !selectedSlot.value) return true; // Disponible si no hay fecha/hora
  const targets = targetDatesForSelectedDay.value;

  return !occupiedClasses.value.some(c => 
    c.profesor_id === profesorId &&
    c.fecha_hora && 
    targets.some(t => c.fecha_hora.startsWith(t)) && 
    c.time === selectedSlot.value
  );
};

const submitForm = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  const missing = [];
  if (!form.activity_id) missing.push("actividad");
  if (selectedDayOfWeek.value === null) missing.push("día");
  if (!selectedSlot.value) missing.push("hora");
  if (!selectedRoom.value) missing.push("salón");
  if (!form.profesor_id) missing.push("profesor");

  if (missing.length > 0) {
    errorMessage.value = `Por favor seleccione ${missing.join(", ")}.`;
    return;
  }

  if (form.cupoMaximo > 20) {
    errorMessage.value = "La capacidad máxima del salón es de 20 cupos";
    return;
  }

  if (form.cupoMaximo < 1) {
    errorMessage.value = "La capacidad mínima del salón es de 1 cupo";
    return;
  }

  try {
    let targetDates = targetDatesForSelectedDay.value;

    // Comprobar conflictos de salón por si acaso antes de crear
    const conflicts = targetDates.filter(fechaStr =>
      occupiedClasses.value.some(c => c.fecha_hora && c.fecha_hora.startsWith(fechaStr) && c.time === selectedSlot.value && c.room === selectedRoom.value)
    );

    if (conflicts.length > 0) {
      errorMessage.value = `Conflicto de salón en estas fechas: ${conflicts.join(', ')}.`;
      return;
    }

    const createdDates = [];
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    
    for (const fechaStr of targetDates) {
      try {
        await axios.post(`${baseURL}/classes`, {
          activity_id: Number(form.activity_id),
          date: fechaStr,
          time: selectedSlot.value,
          room: selectedRoom.value,
          cupoMaximo: form.cupoMaximo,
          profesor_id: form.profesor_id,
        }, { withCredentials: true });
        createdDates.push(fechaStr);
      } catch (err) {
        // Si una de las fechas falla (ej. conflicto de profesor), mostramos el error y paramos.
        const specificError = err.response?.data?.error;
        if (specificError) {
          errorMessage.value = specificError;
          return; // Detiene el bucle
        }
      }
    }

    successMessage.value = createdDates.length > 0 ? `Clases generadas con éxito para las fechas: ${createdDates.join(' | ')}.` : 'No se crearon clases.';
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
  border-color: #9f5f91;
  background-color: #f5e6f5;
  color: #572c57;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(87, 44, 87, 0.2);
}

.day-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.day-btn {
  padding: 1rem 0.75rem;
  transition: all 0.25s ease;
}

.day-btn.active {
  border-color: #9f5f91;
  background-color: #f5e6f5;
  color: #572c57;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(87, 44, 87, 0.2);
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
  border-color: #9f5f91;
  background-color: #f5e6f5;
  color: #572c57;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(87, 44, 87, 0.2);
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
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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

.input-hint {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.profesor-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #d0c0d0;
  border-radius: 8px;
  font-size: 1rem;
  background-color: white;
  color: #333;
}

.btn-inscribe {
  width: 100%;
  transition: all 0.3s ease;
}

.btn-inscribe:disabled {
  background-color: #e5e7eb !important;
  color: #9ca3af !important;
  border-color: #e5e7eb !important;
  cursor: not-allowed;
  box-shadow: none !important;
  transform: none !important;
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
  
  .day-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .slots-grid {
    grid-template-columns: 1fr;
  }
}
</style>
