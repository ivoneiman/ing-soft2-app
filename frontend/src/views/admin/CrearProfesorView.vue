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
import { reactive, ref } from 'vue';
import axios from 'axios';

const form = reactive({
  nombre: '',
  apellido: '',
});

const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const submitForm = async () => {
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    const response = await axios.post(`${baseURL}/profesores`, {
      nombre: form.nombre,
      apellido: form.apellido,
    }, { withCredentials: true });

    successMessage.value = response.data.message;
    // Limpiar formulario
    form.nombre = '';
    form.apellido = '';
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Ocurrió un error inesperado.';
  } finally {
    loading.value = false;
  }
};
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
.form-group input { padding: 0.75rem 1rem; border: 1px solid #d0c0d0; border-radius: 8px; font-size: 1rem; }
.btn-primary { padding: 0.8rem 1.5rem; font-size: 1rem; align-self: flex-start; }
.success-message, .error-message { margin-top: 1.5rem; padding: 1rem; border-radius: 8px; font-weight: 500; }
</style>