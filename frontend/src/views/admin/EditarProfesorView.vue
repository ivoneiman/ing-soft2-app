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
        <div v-if="profesorActual" class="current-info">
          <strong>Nombre y Apellido actuales:</strong> {{ profesorActual.nombre }} {{ profesorActual.apellido }}
          <br />
          <strong>Actividad/es actual/es:</strong> {{ actividadesActualesTexto }}
        </div>

        <div class="input-group">
          <label for="nombre">Nombre</label>
          <input
            id="nombre"
            v-model="form.nombre"
            type="text"
            placeholder="Ej: Carlos"
            required
            :disabled="loading || loadError"
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
            :disabled="loading || loadError"
          />
        </div>

        <div class="input-group">
          <label>Seleccionar la/s actividad/es que dictará el profesor</label>
          <div class="activity-toggle-grid">
            <button
              v-for="actividad in actividades"
              :key="actividad.id"
              type="button"
              class="activity-toggle-btn"
              :class="{ active: form.actividad_ids.includes(actividad.id) }"
              :disabled="loading || loadError"
              @click="toggleActividad(actividad.id)"
            >
              {{ actividad.name }}
            </button>
          </div>
        </div>

        <div v-if="errorMessage" class="msg error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="msg success">{{ successMessage }}</div>

        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="router.push('/admin/profesores/listar')">
            Volver al listado
          </button>
          <button type="submit" class="btn-primary" :disabled="loading || loadError">
            {{ loadError ? 'Edición no disponible' : (loading ? 'Guardando...' : 'Guardar Cambios') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { getActivities } from '@/services/api.js';

const route = useRoute();
const router = useRouter();
const profesorId = route.params.id;

const form = reactive({
  nombre: '',
  apellido: '',
  actividad_ids: [],
});

const profesorActual = ref(null);
const actividades = ref([]);
const initialLoading = ref(true);
const loading = ref(false);
const loadError = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const actividadesActualesTexto = computed(() => {
  const nombres = profesorActual.value?.actividades?.map(a => a.name) || [];
  return nombres.length ? nombres.join(', ') : 'Sin asignar';
});

const toggleActividad = (actividadId) => {
  const index = form.actividad_ids.indexOf(actividadId);
  if (index === -1) {
    form.actividad_ids.push(actividadId);
  } else {
    form.actividad_ids.splice(index, 1);
  }
};

onMounted(async () => {
  try {
    const [profesorResponse, actividadesResponse] = await Promise.all([
      axios.get(`${baseURL}/profesores/${profesorId}`, { withCredentials: true }),
      getActivities(),
    ]);
    const profesor = profesorResponse.data.profesor;
    profesorActual.value = profesor;
    form.actividad_ids = (profesor.actividades || []).map(a => a.id);
    actividades.value = actividadesResponse.data || [];
  } catch (err) {
    loadError.value = true;
    errorMessage.value = err.response?.data?.error || 'No se pudieron cargar los datos del profesor.';
    console.error(err);
  } finally {
    initialLoading.value = false;
  }
});

async function handleSubmit() {
  if (initialLoading.value || loadError.value) return;

  errorMessage.value = '';
  successMessage.value = '';

  if (form.actividad_ids.length === 0) {
    errorMessage.value = 'Debe seleccionar al menos una actividad para el profesor.';
    return;
  }

  loading.value = true;

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

.current-info {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: #572c57;
  border-radius: 10px;
  color: #f5f0f7;
}

.activity-toggle-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

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

.activity-toggle-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>