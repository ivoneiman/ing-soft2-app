<template>
  <div class="admin-view">
    <!-- Modal de Información -->
    <div v-if="selectedProfesor" class="modal-backdrop" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3 class="modal-title">Información de {{ selectedProfesor.nombre }} {{ selectedProfesor.apellido }}</h3>
        <div class="modal-body">
          <h4>Clases Asignadas</h4>
          <ul v-if="selectedProfesor.clases_resumen && selectedProfesor.clases_resumen.length > 0" class="clases-list">
            <li v-for="(resumen, index) in selectedProfesor.clases_resumen" :key="index" v-html="resumen"></li>
          </ul>          
          <p v-else>No tiene clases asignadas.</p>
        </div>
        <div class="modal-footer">
          <button @click="closeModal" class="btn-secondary">Cerrar</button>
        </div>
      </div>
    </div>

    <header class="admin-header">
      <h1>Listado de Profesores</h1>
      <p class="lead">Aquí podés ver todos los profesores cargados en el sistema.</p>
    </header>

    <div class="admin-card">
      <div v-if="loading" class="loading-state">
        <p>Cargando profesores...</p>
      </div>
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
      </div>
      <div v-else-if="profesores.length === 0" class="empty-state">
        <p>No hay profesores cargados en el sistema.</p>
        <RouterLink to="/admin/profesores/crear" class="btn-primary">Cargar primer profesor</RouterLink>
      </div>
      <div v-else class="table-responsive">
        <table class="user-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Apellido</th>
              <th class="actions-column">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="profesor in profesores" :key="profesor.id">
              <td>{{ profesor.id }}</td>
              <td>{{ profesor.nombre }}</td>
              <td>{{ profesor.apellido }}</td>
              <td class="actions-column">
               <button @click="showInfo(profesor)" class="btn-action btn-info">Ver Info</button>
                <RouterLink :to="`/admin/profesores/editar/${profesor.id}`" class="btn-action btn-edit">Editar</RouterLink>
                <button @click="deleteProfesor(profesor.id)" class="btn-action btn-delete">Borrar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { RouterLink } from 'vue-router';
import axios from 'axios';

const profesores = ref([]);
const loading = ref(true);
const error = ref('');
const selectedProfesor = ref(null);
const baseURL = computed(() => import.meta.env.VITE_API_URL || 'http://localhost:5000/api');

async function fetchProfesores() {
  loading.value = true;
  error.value = '';
  try {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    const response = await axios.get(`${baseURL}/profesores`, { withCredentials: true });
    profesores.value = response.data.profesores;
  } catch (err) {
    error.value = err.response?.data?.error || 'No se pudo cargar la lista de profesores.';
    console.error(err);
  } finally {
    loading.value = false;
  }
}

function showInfo(profesor) {
  selectedProfesor.value = profesor;
}

function closeModal() {
  selectedProfesor.value = null;
}

async function deleteProfesor(profesorId) {
  if (!confirm('¿Estás seguro de que querés eliminar a este profesor?')) {
    return;
  }

  try {
    await axios.delete(`${baseURL.value}/profesores/${profesorId}`, { withCredentials: true });
    // Actualizar la lista localmente para reflejar el cambio
    profesores.value = profesores.value.filter(p => p.id !== profesorId);
    alert('Profesor eliminado exitosamente.');
  } catch (err) {
    const errorMessage = err.response?.data?.error || 'No se pudo eliminar el profesor.';
    alert(`Error: ${errorMessage}`);
  }
}

function formatFecha(fechaIso) {
  if (!fechaIso) return 'Fecha no definida';
  const date = new Date(fechaIso);
  return date.toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

onMounted(fetchProfesores);
</script>

<style scoped>
.admin-view {
  padding: 24px;
  max-width: 900px;
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
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 2rem;
  color: #572c57;
}

.empty-state .btn-primary {
  margin-top: 1rem;
}

.table-responsive {
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  color: #333; /* Color de texto oscuro para la tabla */
}

.user-table th,
.user-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e8dce8;
  text-align: left;
}

.user-table th {
  background-color: #f5e6f5;
  color: #572c57;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.85rem;
}
.user-table tbody tr:hover {
  background-color: #fdfaff;
}
.user-table td {
  transition: background-color 0.2s ease;
}

.actions-column {
  text-align: center;
}

.actions-container {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  text-align: center;
  transition: all 0.2s ease;
}

.btn-info {
  background-color: #eef2ff;
  color: #4338ca;
}
.btn-info:hover {
  background-color: #c7d2fe;
}

.btn-edit {
  background-color: #fefce8;
  color: #a16207;
}
.btn-edit:hover {
  background-color: #fef08a;
}

.btn-delete {
  background-color: #fee2e2;
  color: #b91c1c;
}
.btn-delete:hover {
  background-color: #fecaca;
}

/* Estilos del Modal */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 1.5rem 2rem;
  border-radius: 12px;
  min-width: 400px;
  max-width: 90%;
  color: #333;
}

.modal-title {
  color: #572c57;
  margin-top: 0;
  margin-bottom: 1.5rem;
}

.modal-footer {
  margin-top: 1.5rem;
  text-align: right;
}

.clases-list {
  list-style-type: none;
  padding-left: 0;
  margin: 0;
  font-size: 0.9rem;
  color: #4a3a4a;
}

.clases-list li {
  padding: 6px 0;
  border-bottom: 1px solid #f0e6f0;
}

.clases-list li:last-child {
  border-bottom: none;
}

.modal-body h4 {
  color: #572c57;
  margin-bottom: 1rem;
  border-bottom: 2px solid #e8dce8;
  padding-bottom: 0.5rem;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}
</style>