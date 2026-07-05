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
      <div class="search-container">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Buscar usuario por nombre, apellido o email..." 
          class="search-input"
        />
      </div>

      <div v-if="isLoading" class="empty-state mt-4">Cargando directorio...</div>
      <div v-else-if="filteredUsers.length === 0" class="empty-state mt-4">No se encontraron usuarios.</div>

      <table v-else class="users-table mt-4">
        <thead>
          <tr>
            <th>Rol</th>
            <th>Apellido y Nombre</th>
            <th>Email</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td><span :class="['role-pill', user.role]">{{ roleLabel(user.role) }}</span></td>
            <td class="bold">{{ formatName(user.apellido, user.username) }}</td>
            <td>{{ user.email }}</td>
            <td>
              <div class="actions-group">
                <button class="table-action secondary" @click="openUserProfile(user.id)">
                  Información del perfil
                </button>
                <button class="table-action danger" @click="openDeleteConfirmation(user)">Eliminar</button>
              </div>
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
              <p>{{ formatName(selectedUser.user.apellido, selectedUser.user.username) }}</p>
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
                <tr v-for="enr in selectedUser.enrollments" :key="enr.id" :class="{'is-cancelled': isCancelled(enr)}">
                  <td class="bold">{{ enr.actividad }}</td>
                  <td>{{ formatDateTime(enr.fecha_hora) }}</td>
                  <td>{{ enr.tipo }}</td>
                  <td>
                    <template v-if="isCancelled(enr)">
                      <span v-if="enr.requiere_reembolso" class="status-pill expired">Cancelada (Reembolso pendiente)</span>
                      <span v-else-if="enr.estado_pago === 'PAID'" class="status-pill expired">Cancelada (Créditos devueltos)</span>
                      <span v-else class="status-pill expired">Cancelada</span>
                    </template>
                    <template v-else>
                      <span :class="['status-pill', (enr.estado_pago || '').toLowerCase()]">{{ paymentStatusLabel(enr.estado_pago) }}</span>
                    </template>
                  </td>
                  <td>
                    <span v-if="isCancelled(enr)">-</span>
                    <span v-else>{{ formatMoney(enr.monto_total) }}</span>
                  </td>
                  <td :class="{'debt': Number(enr.saldo) > 0 && !isCancelled(enr)}">
                    <span v-if="isCancelled(enr)">-</span>
                    <span v-else>{{ formatMoney(enr.saldo) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>

    <!-- Modal de Confirmación de Eliminación -->
    <div v-if="userToDelete" class="modal-backdrop" role="dialog" aria-modal="true" @click.self="closeDeleteConfirmation">
      <section class="profile-modal delete-confirm">
        <header class="modal-header">
          <h2>Confirmar Eliminación</h2>
          <button class="close-btn" @click="closeDeleteConfirmation">✕</button>
        </header>
        <div class="modal-body">
          <p>
            ¿Estás seguro de que deseas eliminar permanentemente al usuario <strong>{{ formatName(userToDelete.apellido, userToDelete.username) }}</strong>?
          </p>
          <p class="warning-text">
            Toda su información, incluyendo inscripciones y pagos, será eliminada. Esta acción no se puede deshacer.
          </p>
          <p v-if="deleteErrorMessage" class="delete-error-message">
            {{ deleteErrorMessage }}
          </p>
          <p v-if="deleteSuccessMessage" class="delete-success-message">
            {{ deleteSuccessMessage }}
          </p>
        </div>
        <footer class="modal-footer">
            <button class="btn-secondary" @click="closeDeleteConfirmation">{{ deleteSuccessMessage ? 'Cerrar' : 'Cancelar' }}</button>
            <button v-if="!deleteSuccessMessage" class="btn-danger" @click="confirmDeleteUser" :disabled="isDeleting">
              {{ isDeleting ? 'Eliminando...' : 'Sí, eliminar usuario' }}
            </button>
        </footer>
      </section>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { deleteUserAsAdmin } from '../../services/api';
import { formatDateTime, formatMoney } from '../../utils/formatters';

// Para no depender de que modifiques tu api.js, hacemos la llamada directamente configurada.
// Ajusta la URL base si la tienes en variables de entorno, por defecto apuntará al origin local.
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const users = ref([]);
const isLoading = ref(false);
const searchQuery = ref('');

const userToDelete = ref(null);
const isDeleting = ref(false);
const deleteErrorMessage = ref('');
const deleteSuccessMessage = ref('');

const filteredUsers = computed(() => {
  let result = [...users.value];

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase().trim();
    result = result.filter(user => {
      const fullName = `${user.username || ''} ${user.apellido || ''}`.toLowerCase();
      const reversedName = `${user.apellido || ''} ${user.username || ''}`.toLowerCase();
      
      return fullName.includes(query) ||
             reversedName.includes(query) ||
             (user.email && user.email.toLowerCase().includes(query)) ||
             (user.dni && user.dni.toLowerCase().includes(query));
    });
  }

  // Ordenar por jerarquía de rol, y luego alfabéticamente por apellido
  const roleOrder = { admin: 1, employee: 2, client: 3 };
  
  return result.sort((a, b) => {
    const roleA = roleOrder[a.role] || 4;
    const roleB = roleOrder[b.role] || 4;
    if (roleA !== roleB) return roleA - roleB;
    
    const apA = (a.apellido || '').trim();
    const apB = (b.apellido || '').trim();
    return apA.localeCompare(apB, 'es', { sensitivity: 'base' });
  });
});

const selectedUser = ref(null);
const isLoadingProfile = ref(false);

function isCancelled(enr) {
  const estadoInsc = String(enr.estado_inscripcion || '').toLowerCase();
  const estadoClas = String(enr.estado_clase || '').toLowerCase();
  return ['cancelada', 'cancelled'].includes(estadoInsc) || ['cancelada', 'cancelled'].includes(estadoClas);
}

function roleLabel(role) {
  const labels = { admin: 'Administrador', employee: 'Empleado', client: 'Cliente' };
  return labels[role] || role;
}

function paymentStatusLabel(status) {
  const labels = { PENDING: 'Pago Pendiente', PAID: 'Pagado', EXPIRED: 'Vencido' };
  return labels[status] || status;
}

function formatName(apellido, nombre) {
  const formatWord = (w) => (w ? w.toString().toLowerCase().replace(/\b\w/g, l => l.toUpperCase()) : '');
  return `${formatWord(apellido)} ${formatWord(nombre)}`.trim();
}

async function loadUsers() {
  isLoading.value = true;
  try {
    const response = await axios.get(`${baseURL}/users`, { withCredentials: true });
    users.value = response.data || [];
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

function openDeleteConfirmation(user) {
  userToDelete.value = user;
  deleteErrorMessage.value = '';
  deleteSuccessMessage.value = '';
}

function closeDeleteConfirmation() {
  userToDelete.value = null;
  deleteErrorMessage.value = '';
  deleteSuccessMessage.value = '';
}

async function confirmDeleteUser() {
  if (!userToDelete.value) return;

  isDeleting.value = true;
  deleteErrorMessage.value = '';
  try {
    const response = await deleteUserAsAdmin(userToDelete.value.id);

    // Eliminar el usuario de la lista local para actualizar la UI al instante
    users.value = users.value.filter(u => u.id !== userToDelete.value.id);
    deleteSuccessMessage.value = response.data?.message || 'Usuario eliminado correctamente.';
  } catch (err) {
    console.error("Error eliminando el usuario:", err);
    deleteErrorMessage.value = err.response?.data?.error || 'No se puede eliminar el usuario porque tiene inscripciones activas o pagos aprobados.';
  } finally {
    isDeleting.value = false;
  }
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
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.users-table th {
  padding: 14px 12px;
  border-bottom: 2px solid #e8dce8;
  text-align: left;
  color: #572c57;
  font-weight: 700;
  font-size: 0.95rem;
}

.users-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #e8dce8;
  text-align: left;
  font-size: 0.95rem;
  vertical-align: middle;
}

.actions-group {
  display: flex;
  gap: 0.5rem;
}

.search-container {
  margin-bottom: 1rem;
}
.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d0c0d0;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  color: #4a3a4a;
  transition: border-color 0.2s;
}
.search-input:focus {
  border-color: #9f5f91;
}
.mt-4 {
  margin-top: 1.5rem;
}
.is-cancelled td {
  opacity: 0.6;
  background-color: #fafafa;
}
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
.table-action.danger {
  background-color: #fee2e2;
  color: #b42318;
}


.modal-backdrop {
  position: fixed; inset: 0; background: rgba(20, 10, 20, 0.72);
  display: flex; align-items: center; justify-content: center; z-index: 50; padding: 1rem;
}

.profile-modal {
  background: #fff; border-radius: 12px; width: 100%; max-width: 800px;
  max-height: 90vh; overflow-y: auto;
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e8dce8;
  background-color: #f9fafb;
}
.modal-footer button {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 1px solid;
  cursor: pointer;
  font-weight: 600;
}
.btn-secondary { background-color: #fff; border-color: #d0d5dd; color: #344054; }
.btn-danger { background-color: #d92d20; border-color: #d92d20; color: #fff; }

.warning-text {
  background-color: #fffbeb;
  color: #b42318;
}

.delete-error-message {
  background-color: #fee2e2;
  color: #b42318;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
}

.delete-success-message {
  background-color: #eef8f1;
  color: #027a48;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
}

.classes-title { color: #572c57; margin-bottom: 1rem;}

.status-pill { padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
.status-pill.pending { background: #fef0c7; color: #b54708; }
.status-pill.paid { background: #eef8f1; color: #027a48; }
.status-pill.expired { background: #fee2e2; color: #b42318; }
.debt { color: #b42318; font-weight: 700; }
</style>
