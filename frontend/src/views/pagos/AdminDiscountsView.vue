<!--
  Vista para que el Administrador gestione los descuentos de las clases.
  Cumple con los Criterios de Aceptación de la HU de promociones.
  Lógica mejorada: permite ver todas las clases y muestra el estado del descuento.
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
          <option v-for="clase in all_classes" :key="clase.id" :value="clase.id">
            {{ clase.actividad || clase.name }} - {{ formatDate(clase.fecha_hora) }}
          </option>
        </select>
      </div>

      <!-- Sección de descuento (solo si se ha seleccionado una clase) -->
      <div v-if="selectedClass">
        <!-- Mensaje si la clase ya tiene ambos descuentos (40 + 70 = 110) -->
        <div v-if="selectedClass.descuento === 110" class="info-msg">
          Descuentos ya aplicados
        </div>

        <!-- Formulario para aplicar el/los descuento/s faltante/s -->
        <div v-else>
          <!-- 2. Porcentaje de descuento -->
          <div class="form-group">
            <label for="discount-input">Porcentaje de Descuento:</label>
            <select id="discount-input" v-model="discountValue" required>
              <option value="" disabled>-- Seleccione el descuento --</option>
              <option v-if="selectedClass.descuento !== 40" value="40">40% (Aplica para días 15 al 20)</option>
              <option v-if="selectedClass.descuento !== 70" value="70">70% (Aplica para días 21 al fin de mes)</option>
            </select>
          </div>

          <!-- Botón de Confirmación -->
          <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Aplicando...' : 'Confirmar descuento' }}
          </button>
        </div>
      </div>

      <!-- Mensajes de Éxito o Error -->
      <div v-if="successMessage" class="success-msg">{{ successMessage }}</div>
      <div v-if="errorMessage" class="error-msg">{{ errorMessage }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'

// Estados reactivos
const all_classes = ref([])
const selectedClassId = ref('')
const discountValue = ref('')

const loading = ref(true)
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Función para cargar las clases desde el backend
const fetchClasses = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await fetch('http://localhost:5000/api/catalog', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    
    const data = await response.json()
    if (response.ok) {
      all_classes.value = data.classes || []
    } else {
      errorMessage.value = data.error || 'Error al cargar las clases.'
    }
  } catch (error) {
    errorMessage.value = 'Error de conexión al cargar clases.'
  } finally {
    loading.value = false;
  }
};

// Cargar las clases al montar el componente
onMounted(fetchClasses);

// Computed: Obtiene el objeto de la clase seleccionada
const selectedClass = computed(() => {
  if (!selectedClassId.value) return null;
  return all_classes.value.find(c => c.id === selectedClassId.value);
});

// Watcher: Resetea la selección de descuento y mensajes cuando cambia la clase
watch(selectedClassId, () => {
  discountValue.value = '';
  successMessage.value = '';
  errorMessage.value = '';
});

// Enviar el descuento al Backend
const onSubmit = async () => {
  successMessage.value = ''
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const response = await fetch(`http://localhost:5000/api/classes/${selectedClassId.value}/discount`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', 
      body: JSON.stringify({ descuento: discountValue.value })
    })

    const data = await response.json()

    if (response.ok) {
      successMessage.value = data.message // "Descuento aplicado con éxito"
      
      // Actualiza el estado local de la clase para reflejar el cambio sumando el descuento aplicado
      const classIndex = all_classes.value.findIndex(c => c.id === selectedClassId.value);
      if (classIndex !== -1) {
        const applied = parseInt(discountValue.value, 10);
        const current = all_classes.value[classIndex].descuento;
        all_classes.value[classIndex].descuento = current === 0 ? applied : 110;
      }
      
      // No reseteamos selectedClassId para que el usuario vea el nuevo estado
      discountValue.value = ''
    } else {
      errorMessage.value = data.error || 'Error al aplicar el descuento.'
    }
  } catch (error) {
    errorMessage.value = 'Error de conexión con el servidor.'
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
.admin-discounts-container { max-width: 500px; margin: 2rem auto; padding: 2rem; border: 1px solid #4a5568; border-radius: 8px; background-color: rgba(0,0,0,0.1); }
.subtitle { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
select { width: 100%; padding: 0.5rem; border-radius: 4px; border: 1px solid #ccc; }
button { width: 100%; padding: 0.75rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
button:disabled { background-color: #999; cursor: not-allowed; }
.success-msg { color: #155724; background-color: #d4edda; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.error-msg { color: #721c24; background-color: #f8d7da; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.info-msg { color: #0c5460; background-color: #d1ecf1; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center; }
.loading { text-align: center; color: #666; padding: 2rem; }
</style>