<template>
  <div class="admin-view">
    <header class="admin-header">
      <h1>Cargar Nuevo Profesor</h1>
      <p class="lead">Completá los datos para agregar un profesor al sistema.</p>
    </header>

    <div class="admin-card">
      <form @submit.prevent="handleSubmit" class="form-container">
        <div class="input-group">
          <label for="nombre">Nombre</label>
          <input
            id="nombre"
            v-model="form.nombre"
            type="text"
            placeholder="Ej: Juan"
            required
            :disabled="loading"
          />
        </div>

        <div class="input-group">
          <label for="apellido">Apellido</label>
          <input
            id="apellido"
            v-model="form.apellido"
            type="text"
            placeholder="Ej: Pérez"
            required
            :disabled="loading"
          />
        </div>

        <div v-if="error" class="msg error">{{ error }}</div>
        <div v-if="success" class="msg success">{{ success }}</div>

        <div class="form-actions">
          <RouterLink to="/admin/profesores" class="btn-secondary">Volver</RouterLink>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Cargando...' : 'Cargar Profesor' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { RouterLink } from 'vue-router';
import axios from 'axios';

const form = reactive({
  nombre: '',
  apellido: '',
});

const loading = ref(false);
const error = ref('');
const success = ref('');

async function handleSubmit() {
  loading.value = true;
  error.value = '';
  success.value = '';

  if (!form.nombre.trim() || !form.apellido.trim()) {
    error.value = 'Ambos campos son obligatorios.';
    loading.value = false;
    return;
  }

  try {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    const response = await axios.post(`${baseURL}/profesores`, form, { withCredentials: true });
    
    success.value = response.data.message || 'Profesor cargado exitosamente.';
    
    // Limpiar formulario
    form.nombre = '';
    form.apellido = '';

  } catch (err) {
    error.value = err.response?.data?.error || 'No se pudo cargar el profesor.';
    console.error(err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* Reutilizando estilos para consistencia */
.admin-view {
  padding: 24px;
  max-width: 700px;
  margin: 0 auto;
}

.admin-header h1 {
  color: #fff;
  margin-bottom: 0.5rem;
}

.lead {
  color: #e0c0e0;
  margin-bottom: 2rem;
}

.admin-card {
  background: #fff;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  color: #333;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  text-align: center;
}
</style>