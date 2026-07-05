<template>
  <div class="admin-view">
    <header class="admin-header">
      <h1>Editar Perfil del Profesor</h1>
      <p class="lead">Modificá los datos del profesor y guardá los cambios.</p>
    </header>

    <div v-if="initialLoading" class="admin-card">
      <p>Cargando datos del profesor...</p>
    </div>

    <div v-else class="admin-card">
      <form @submit.prevent="handleSubmit" class="form-container">
        <div class="input-group">
          <label for="nombre">Nombre</label>
          <input
            id="nombre"
            v-model="form.nombre"
            type="text"
            placeholder="Ej: Carlos"
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
            placeholder="Ej: Gómez"
            required
            :disabled="loading"
          />
        </div>

        <div v-if="errorMessage" class="msg error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="msg success">{{ successMessage }}</div>

        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="router.push('/admin/profesores/listar')">
            Volver al listado
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Guardando...' : 'Guardar Cambios' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const profesorId = route.params.id;

const form = reactive({
  nombre: '',
  apellido: '',
});

const initialLoading = ref(true);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

onMounted(async () => {
  try {
    const response = await axios.get(`${baseURL}/profesores/${profesorId}`, { withCredentials: true });
    const profesor = response.data.profesor;
    form.nombre = profesor.nombre;
    form.apellido = profesor.apellido;
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'No se pudieron cargar los datos del profesor.';
    console.error(err);
  } finally {
    initialLoading.value = false;
  }
});

async function handleSubmit() {
  loading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const response = await axios.put(`${baseURL}/profesores/${profesorId}`, form, { withCredentials: true });
    successMessage.value = response.data.message || 'Perfil actualizado correctamente.';
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'No se pudo actualizar el perfil.';
    console.error(err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
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