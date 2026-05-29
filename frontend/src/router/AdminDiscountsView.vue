<!--
  Vista para que el Administrador gestione los descuentos de las clases.
  Cumple con los Criterios de Aceptación de la HU de promociones.
-->
<template>
  <div class="admin-discounts-container">
    <h2>Configurar Descuentos</h2>
    <p class="subtitle">Aplica promociones a las clases según la fecha.</p>

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
          <option v-for="clase in classes" :key="clase.id" :value="clase.id">
            {{ clase.actividad || clase.name }} - {{ formatDate(clase.fecha_hora) }}
          </option>
        </select>
      </div>

      <!-- 2. Porcentaje de descuento -->
      <div class="form-group">
        <label for="discount-input">Porcentaje de Descuento (%):</label>
        <select id="discount-input" v-model="discountValue" required>
          <option value="" disabled>-- Seleccione el descuento --</option>
          <option value="40">40% (Aplica para días 15 al 20)</option>
          <option value="70">70% (Aplica para días 21 al fin de mes)</option>
          <option value="0">0% (Sin descuento)</option>
        </select>
      </div>

      <!-- Botón de Confirmación -->
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Aplicando...' : 'Confirmar descuento' }}
      </button>

      <!-- Mensajes de Éxito o Error -->
      <div v-if="successMessage" class="success-msg">{{ successMessage }}</div>
      <div v-if="errorMessage" class="error-msg">{{ errorMessage }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { applyClassDiscount, getCatalog } from '../services/api'

// Estados reactivos
const classes = ref([])
const selectedClassId = ref('')
const discountValue = ref('')

const loading = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Cargar las clases al montar el componente (usamos el catálogo disponible)
onMounted(async () => {
  try {
    const { data } = await getCatalog()
    classes.value = data.classes || []
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Error de conexión al cargar clases.'
  } finally {
    loading.value = false
  }
})

// Enviar el descuento al Backend
const onSubmit = async () => {
  successMessage.value = ''
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const { data } = await applyClassDiscount(selectedClassId.value, discountValue.value)
    successMessage.value = data.message
    selectedClassId.value = ''
    discountValue.value = ''
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Error de conexión con el servidor.'
  } finally {
    isSubmitting.value = false
  }
}

// Utilidad para formatear la fecha visualmente ("15/05/2026 10:00")
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('es-AR', { 
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute:'2-digit'
  })
}
</script>

<style scoped>
.admin-discounts-container { max-width: 500px; margin: 2rem auto; padding: 2rem; border: 1px solid #eee; border-radius: 8px; }
.subtitle { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
select { width: 100%; padding: 0.5rem; border-radius: 4px; border: 1px solid #ccc; }
button { width: 100%; padding: 0.75rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
button:disabled { background-color: #999; cursor: not-allowed; }
.success-msg { color: #155724; background-color: #d4edda; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.error-msg { color: #721c24; background-color: #f8d7da; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.loading { text-align: center; color: #666; padding: 2rem; }
</style>
