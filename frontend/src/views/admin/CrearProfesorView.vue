<template>
  <div class="profesores-view">
    <header class="view-header">
      <h1>Gestión de Profesores</h1>
      <p class="lead">Crea y administra los profesores del gimnasio.</p>
    </header>

    <div class="card">
      <h2 class="card-title">Cargar Nuevo Profesor</h2>

      <form @submit.prevent="submitForm" class="form-container">
        <div class="form-group">
          <label for="nombre">Nombre</label>
          <input type="text" id="nombre" v-model="form.nombre" placeholder="Ej: Carlos" />
        </div>

        <div class="form-group">
          <label for="apellido">Apellido</label>
          <input type="text" id="apellido" v-model="form.apellido" placeholder="Ej: Méndez" />
        </div>

        <div class="form-group">
          <label>Seleccionar la/s actividad/es que dictará el profesor</label>
          <div class="activity-toggle-grid">
            <button
              v-for="actividad in actividades"
              :key="actividad.id"
              type="button"
              class="activity-toggle-btn"
              :class="{ active: form.actividad_ids.includes(actividad.id) }"
              @click="toggleActividad(actividad.id)"
            >
              {{ actividad.name }}
            </button>
          </div>
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <span v-if="loading">Cargando...</span>
          <span v-else>Cargar Profesor</span>
        </button>
      </form>

      <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import axios from 'axios';
import { getActivities } from '@/services/api.js';

const form = reactive({
  nombre: '',
  apellido: '',
  actividad_ids: [],
});

const actividades = ref([]);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const loadActividades = async () => {
  try {
    const response = await getActivities();
    actividades.value = response.data || [];
  } catch (error) {
    console.error('Error cargando actividades:', error);
    actividades.value = [];
  }
};

const toggleActividad = (actividadId) => {
  const index = form.actividad_ids.indexOf(actividadId);
  if (index === -1) {
    form.actividad_ids.push(actividadId);
  } else {
    form.actividad_ids.splice(index, 1);
  }
};

const submitForm = async () => {
  errorMessage.value = '';
  successMessage.value = '';

  if (form.actividad_ids.length === 0) {
    errorMessage.value = 'Debe seleccionar al menos una actividad para el profesor.';
    return;
  }

  loading.value = true;

  try {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    const response = await axios.post(`${baseURL}/profesores`, {
      nombre: form.nombre,
      apellido: form.apellido,
      actividad_ids: form.actividad_ids,
    }, { withCredentials: true });

    successMessage.value = response.data.message;
    // Limpiar formulario
    form.nombre = '';
    form.apellido = '';
    form.actividad_ids = [];
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Ocurrió un error inesperado.';
  } finally {
    loading.value = false;
  }
};

onMounted(loadActividades);
</script>

<style scoped>
/* Estilos del componente... (sin cambios) */
.profesores-view { padding: 24px; max-width: 800px; margin: 0 auto; }
.view-header h1 { color: #fff; margin-bottom: 0.5rem; }
.lead { color: #e0c0e0; margin-bottom: 2rem; font-size: 1.05rem; }
.card { background: #fff; border-radius: 16px; padding: 2rem; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1); }
.card-title { color: #572c57; margin-bottom: 1.5rem; }
.form-container { display: flex; flex-direction: column; gap: 1.5rem; }
.form-group { display: flex; flex-direction: column; }
.form-group label { margin-bottom: 0.5rem; font-weight: 600; color: #4a3a4a; }
.form-group input, .form-group select { padding: 0.75rem 1rem; border: 1px solid #d0c0d0; border-radius: 8px; font-size: 1rem; color: #333; background: #fff; }
.activity-toggle-grid { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.activity-toggle-btn {
  padding: 0.75rem 1.25rem;
  border: 1px solid #d0c0d0;
  border-radius: 8px;
  background: #fff;
  color: #4a3a4a;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.activity-toggle-btn.active {
  border-color: #9f5f91;
  background-color: #f5e6f5;
  color: #572c57;
  box-shadow: 0 2px 8px rgba(87, 44, 87, 0.2);
}
.btn-primary { padding: 0.8rem 1.5rem; font-size: 1rem; align-self: flex-start; }
.success-message, .error-message { margin-top: 1.5rem; padding: 1rem; border-radius: 8px; font-weight: 500; }
</style>