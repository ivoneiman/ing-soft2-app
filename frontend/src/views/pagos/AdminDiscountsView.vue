<!--
  Vista para que el Administrador gestione los descuentos de las clases.
  Cumple con los Criterios de Aceptación de la HU de promociones.
  Permite ver todas las clases y configurar el descuento vigente.
-->
<template>
  <div class="admin-discounts-container">
    <h2>Configurar Descuentos</h2>
    <p class="subtitle">Aplica o visualiza promociones en las clases.</p>

    <!-- Estado de carga inicial -->
    <div v-if="loading" class="loading">
      Cargando clases disponibles...
    </div>

    <!-- Formulario de Descuentos -->
    <form v-else @submit.prevent="onSubmit">
      
      <!-- 1. Selección de Clase -->
      <div class="form-group">
        <label for="class-select">Seleccionar Clase:</label>
        <select id="class-select" v-model="selectedClassId" required>
          <option value="" disabled>-- Seleccione una clase --</option>
          <option v-for="clase in allClasses" :key="clase.id" :value="clase.id">
            {{ clase.actividad || clase.name }} - {{ formatDateTime(clase.fecha_hora) }}
          </option>
        </select>
      </div>

      <!-- Sección de descuento (solo si se ha seleccionado una clase) -->
      <div v-if="selectedClass">
        <div class="form-group">
          <label for="discount-input">Porcentaje de Descuento:</label>
          <select id="discount-input" v-model="discountValue" required>
            <option value="" disabled>-- Seleccione el descuento --</option>
            <option
              v-for="option in discountOptions"
              :key="option.percentage"
              :value="String(option.percentage)"
              :disabled="selectedClass.descuento === option.percentage"
            >
              {{ option.label }}
            </option>
          </select>
        </div>

        <div v-if="discountValue === ''" class="info-msg">
          Descuento actual: {{ Number(selectedClass.descuento || 0) }}%
        </div>

        <button type="submit" :disabled="isSubmitting || discountValue === ''">
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
import { applyClassDiscount, getAllClasses, getPaymentDiscountRules } from '../../services/api'
import { formatDateTime } from '../../utils/formatters'

const allClasses = ref([])
const selectedClassId = ref('')
const discountValue = ref('')
const discountRules = ref({ periods: [] })

const loading = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const fetchClasses = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const [classesResponse, rulesResponse] = await Promise.all([
      getAllClasses(),
      getPaymentDiscountRules(),
    ])
    allClasses.value = classesResponse.data.classes || []
    discountRules.value = rulesResponse.data || { periods: [] }
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Error de conexión al cargar clases.'
  } finally {
    loading.value = false;
  }
};

onMounted(fetchClasses);

const selectedClass = computed(() => {
  if (!selectedClassId.value) return null;
  return allClasses.value.find(c => c.id === Number(selectedClassId.value));
});

const discountOptions = computed(() =>
  discountRules.value.periods.map((period) => ({
    percentage: period.percentage,
    label: `${period.percentage}% (días ${period.start_day} al ${period.end_day})`,
  }))
);

watch(selectedClassId, () => {
  discountValue.value = '';
  successMessage.value = '';
  errorMessage.value = '';
});

const onSubmit = async () => {
  successMessage.value = ''
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const response = await applyClassDiscount(selectedClassId.value, Number(discountValue.value))
    successMessage.value = response.data.message

    const classIndex = allClasses.value.findIndex(c => c.id === Number(selectedClassId.value));
    if (classIndex !== -1 && response.data.class) {
      allClasses.value[classIndex] = response.data.class;
    }

    discountValue.value = ''
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
