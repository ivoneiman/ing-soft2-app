<!--
  Vista para que el Administrador gestione los descuentos de las clases.
  Cumple con los Criterios de Aceptación de la HU de promociones.
  Permite ver todas las clases y configurar el descuento vigente.
-->
<template>
  <div class="admin-discounts-container">
    <h2>Configurar Descuentos</h2>
    <p class="subtitle">Aplica promociones a todos los turnos de la semana para un horario específico.</p>

    <!-- Estado de carga inicial -->
    <div v-if="loading" class="loading">
      Cargando clases disponibles...
    </div>

    <!-- Formulario de Descuentos -->
    <form v-else @submit.prevent="onSubmit">
      
      <!-- 1. Selección de Actividad -->
      <div class="form-group">
        <label for="activity-select">1. Seleccionar Actividad:</label>
        <select id="activity-select" v-model="selectedActivityName" required>
          <option value="" disabled>-- Seleccione una actividad --</option>
          <option v-for="act in availableActivities" :key="act.id" :value="act.id">
            {{ act.name }}
          </option>
        </select>
      </div>

      <!-- 2. Selección de Día -->
      <div class="form-group" v-if="selectedActivityName">
        <label for="day-select">2. Seleccionar Día:</label>
        <select id="day-select" v-model="selectedWeekday" required>
          <option value="" disabled>-- Seleccione un día --</option>
          <option v-for="day in availableWeekdays" :key="day.value" :value="day.value">
            Todos los {{ day.label }}
          </option>
        </select>
      </div>

      <!-- 3. Selección de Horario -->
      <div class="form-group" v-if="selectedWeekday !== ''">
        <label for="time-select">3. Seleccionar Horario:</label>
        <select id="time-select" v-model="selectedTime" required>
          <option value="" disabled>-- Seleccione un horario --</option>
          <option v-for="time in availableTimes" :key="time" :value="time">
            A las {{ time }}
          </option>
        </select>
      </div>

      <!-- 4. Sección de descuento -->
      <div v-if="representativeClass">
        <div class="info-msg" style="margin-bottom: 1rem;">
          Se aplicará automáticamente un descuento del <strong>40%</strong> (días 15 al 21) y <strong>70%</strong> (día 22 en adelante) a todas las clases futuras en este horario.
        </div>

        <button type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Aplicando...' : 'Confirmar descuento' }}
        </button>
      </div>

      <!-- Mensajes de Éxito o Error -->
      <div v-if="successMessage" class="success-msg">{{ successMessage }}</div>
      <div v-if="errorMessage" class="error-msg">{{ errorMessage }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { applyClassDiscount, getAllClasses } from '../../services/api'

const allClasses = ref([])
const selectedActivityName = ref('')
const selectedWeekday = ref('')
const selectedTime = ref('')

const loading = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const fetchClasses = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const classesResponse = await getAllClasses()
    allClasses.value = classesResponse.data.classes || []
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Error de conexión al cargar clases.'
  } finally {
    loading.value = false;
  }
};

onMounted(fetchClasses);

const availableActivities = computed(() => {
  const acts = new Set()
  allClasses.value.forEach(c => {
    const actName = c.actividad || c.name;
    if (actName) {
      acts.add(actName)
    }
  })
  return Array.from(acts).sort().map(name => ({ id: name, name }))
});

const availableWeekdays = computed(() => {
  if (!selectedActivityName.value) return []
  const days = new Set()
  allClasses.value.forEach(c => {
    const actName = c.actividad || c.name;
    if (actName === selectedActivityName.value && c.fecha_hora) {
      days.add(new Date(c.fecha_hora).getDay())
    }
  })
  return Array.from(days).sort((a,b) => a - b).map(d => ({ value: d, label: getWeekdayName(d) }))
})

const availableTimes = computed(() => {
  if (selectedWeekday.value === '') return []
  const times = new Set()
  allClasses.value.forEach(c => {
    const actName = c.actividad || c.name;
    if (
      actName === selectedActivityName.value && 
      c.fecha_hora && 
      new Date(c.fecha_hora).getDay() === Number(selectedWeekday.value)
    ) {
      times.add(getTime(c.fecha_hora))
    }
  })
  return Array.from(times).sort()
})

const representativeClass = computed(() => {
  if (!selectedTime.value) return null
  return allClasses.value.find(c => 
    (c.actividad || c.name) === selectedActivityName.value &&
    c.fecha_hora &&
    new Date(c.fecha_hora).getDay() === Number(selectedWeekday.value) &&
    getTime(c.fecha_hora) === selectedTime.value
  )
});

const getWeekdayName = (dayIndex) => {
  const days = ["Domingos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábados"];
  return days[dayIndex];
};

const getTime = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
};

watch(selectedActivityName, () => {
  selectedWeekday.value = '';
  selectedTime.value = '';
  successMessage.value = '';
  errorMessage.value = '';
});

watch(selectedWeekday, () => {
  selectedTime.value = '';
  successMessage.value = '';
  errorMessage.value = '';
});

watch(selectedTime, () => {
  successMessage.value = '';
  errorMessage.value = '';
});

const onSubmit = async () => {
  if (!representativeClass.value) return;
  
  successMessage.value = ''
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    // Pasamos un "0" o null como segundo argumento para no romper la petición wrapper genérica de api.js, el backend lo ignorará.
    const response = await applyClassDiscount(representativeClass.value.id, 0)
    successMessage.value = response.data.message
    
    await fetchClasses()
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Error de conexión con el servidor.'
  } finally {
    isSubmitting.value = false
  }
}

</script>

<style scoped>
.admin-discounts-container { max-width: 500px; margin: 2rem auto; padding: 2rem; border: 1px solid #4a5568; border-radius: 8px; background-color: rgba(0,0,0,0.1); }
.subtitle { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
select { width: 100%; padding: 0.5rem; border-radius: 4px; border: 1px solid #ccc; }
button { width: 100%; }
button:disabled { cursor: not-allowed; }
.success-msg { color: #155724; background-color: #d4edda; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.error-msg { color: #721c24; background-color: #f8d7da; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.info-msg { color: #0c5460; background-color: #d1ecf1; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.loading { text-align: center; color: #666; padding: 2rem; }
</style>
