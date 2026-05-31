<template>
  <main class="report-view">
    <header class="report-header">
      <div>
        <h1>Directorio de Usuarios</h1>
        <p>Listado completo de administradores, empleados y clientes.</p>
      </div>
      <router-link to="/reportes" class="back-button">
        Volver a Reportes
      </router-link>
    </header>

    <section class="table-section">
      <div v-if="isLoading" class="empty-state">Cargando directorio...</div>
      <div v-else-if="users.length === 0" class="empty-state">No se encontraron usuarios.</div>

      <table v-else class="users-table">
        <thead>
          <tr>
            <th>Rol</th>
            <th>Apellido y Nombre</th>
            <th>Email</th>
            <th>DNI</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td><span :class="['role-pill', user.role]">{{ roleLabel(user.role) }}</span></td>
            <td class="bold">{{ user.apellido }} {{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.dni || '-' }}</td>
            <td>
              <button class="table-action secondary" @click="openUserProfile(user.id)">
                Información del perfil
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Modal de Información del Perfil -->
    <div v-if="selectedUser" class="modal-backdrop" role="dialog" aria-modal="true" @click.self="closeUserProfile">
      <section class="profile-modal">
        <header class="modal-header">
          <h2>Información del Perfil</h2>
          <button class="close-btn" @click="closeUserProfile">✕</button>
        </header>

        <div v-if="isLoadingProfile" class="modal-body empty-state">
          Cargando datos del usuario...
        </div>
        <div v-else class="modal-body">
          <div class="profile-details">
            <div class="detail-group">
              <label>Nombre Completo</label>
              <p>{{ selectedUser.user.apellido }} {{ selectedUser.user.username }}</p>
            </div>
            <div class="detail-group">
              <label>Rol asignado</label>
              <p><span :class="['role-pill', selectedUser.user.role]">{{ roleLabel(selectedUser.user.role) }}</span></p>
            </div>
            <div class="detail-group">
              <label>DNI</label>
              <p>{{ selectedUser.user.dni || 'No registrado' }}</p>
            </div>
            <div class="detail-group">
              <label>Teléfono</label>
              <p>{{ selectedUser.user.telefono || 'No registrado' }}</p>
            </div>
            <div class="detail-group">
              <label>Email</label>
              <p>{{ selectedUser.user.email }}</p>
            </div>
          </div>

          <h3 class="classes-title">Clases e Inscripciones</h3>
          <div v-if="selectedUser.enrollments.length === 0" class="empty-state small">
            Este usuario no tiene inscripciones registradas.
          </div>
          <div v-else class="enrollments-list">
            <table class="users-table compact">
              <thead>
                <tr>
                  <th>Actividad</th>
                  <th>Fecha y Hora</th>
                  <th>Tipo</th>
                  <th>Estado</th>
                  <th>Total</th>
                  <th>Saldo</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="enr in selectedUser.enrollments" :key="enr.id">
                  <td class="bold">{{ enr.actividad }}</td>
                  <td>{{ formatDateTime(enr.fecha_hora) }}</td>
                  <td>{{ enr.tipo }}</td>
                  <td><span :class="['status-pill', enr.estado_pago.toLowerCase()]">{{ paymentStatusLabel(enr.estado_pago) }}</span></td>
                  <td>{{ formatMoney(enr.monto_total) }}</td>
                  <td :class="{'debt': Number(enr.saldo) > 0}">{{ formatMoney(enr.saldo) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { formatDateTime, formatMoney } from '../../utils/formatters';

// Para no depender de que modifiques tu api.js, hacemos la llamada directamente configurada.
// Ajusta la URL base si la tienes en variables de entorno, por defecto apuntará al origin local.
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const users = ref([]);
const isLoading = ref(false);

const selectedUser = ref(null);
const isLoadingProfile = ref(false);

function roleLabel(role) {
  const labels = { admin: 'Administrador', employee: 'Empleado', client: 'Cliente' };
  return labels[role] || role;
}

function paymentStatusLabel(status) {
  const labels = { PENDING: 'Pago Pendiente', PAID: 'Pagado', EXPIRED: 'Vencido' };
  return labels[status] || status;
}

async function loadUsers() {
  isLoading.value = true;
  try {
    const response = await axios.get(`${baseURL}/admin/reportes/usuarios`, { withCredentials: true });
    users.value = response.data.users || [];
  } catch (err) {
    console.error("Error cargando directorio de usuarios:", err);
  } finally {
    isLoading.value = false;
  }
}

async function openUserProfile(userId) {
  selectedUser.value = { user: {}, enrollments: [] }; // Placeholder modal
  isLoadingProfile.value = true;
  try {
    const response = await axios.get(`${baseURL}/admin/reportes/usuarios/${userId}/detalles`, { withCredentials: true });
    selectedUser.value = response.data;
  } catch (err) {
    console.error("Error cargando el perfil del usuario:", err);
    selectedUser.value = null;
  } finally {
    isLoadingProfile.value = false;
  }
}

function closeUserProfile() {
  selectedUser.value = null;
}

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.report-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 140px);
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.report-header h1 {
  color: #fff;
  margin: 0 0 0.5rem 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.report-header p {
  color: #e0c0e0;
  font-size: 1.05rem;
  margin: 0;
}

.back-button {
  background: #f6ea98;
  border: none;
  border-radius: 8px;
  color: #572c57;
  font-weight: 700;
  padding: 10px 16px;
  text-decoration: none;
}

.table-section, .empty-state {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.empty-state {
  text-align: center;
  color: #8a6a8a;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  color: #4a3a4a;
}

.users-table th, .users-table td {
  padding: 12px;
  border-bottom: 1px solid #e8dce8;
  text-align: left;
}

.users-table th { color: #572c57; }
.bold { font-weight: 700; }

.role-pill {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}
.role-pill.admin { background: #fee2e2; color: #b42318; }
.role-pill.employee { background: #e0e8f9; color: #1e40af; }
.role-pill.client { background: #eef8f1; color: #027a48; }

.table-action {
  background: #f5e6f5;
  border: none;
  border-radius: 6px;
  color: #572c57;
  cursor: pointer;
  font-weight: 600;
  padding: 8px 12px;
}

.modal-backdrop {
  position: fixed; inset: 0; background: rgba(20, 10, 20, 0.72);
  display: flex; align-items: center; justify-content: center; z-index: 50; padding: 1rem;
}

.profile-modal {
  background: #fff; border-radius: 12px; width: 100%; max-width: 800px;
  max-height: 90vh; overflow-y: auto;
}

.modal-header {
  display: flex; justify-content: space-between; padding: 1.5rem;
  border-bottom: 1px solid #e8dce8;
}
.modal-header h2 { margin: 0; color: #572c57; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #8a6a8a;}

.modal-body { padding: 1.5rem; }
.profile-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;}
.detail-group label { color: #8a6a8a; font-size: 0.85rem; font-weight: 600; display: block; margin-bottom: 4px;}
.detail-group p { margin: 0; font-weight: 700; color: #4a3a4a; }

.classes-title { color: #572c57; margin-bottom: 1rem;}

.status-pill { padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
.status-pill.pending { background: #fef0c7; color: #b54708; }
.status-pill.paid { background: #eef8f1; color: #027a48; }
.status-pill.expired { background: #fee2e2; color: #b42318; }
.debt { color: #b42318; font-weight: 700; }
</style>