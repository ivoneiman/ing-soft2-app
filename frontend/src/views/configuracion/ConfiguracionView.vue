<template>
  <div class="configuracion-view">
    <h1>Edita tu perfil</h1>
    <p class="subtitle">Opciones del sistema</p>

    <!-- Sección de edición de perfil -->
    <section class="profile-section">
      <h2>Editar Perfil</h2>
      
      <!-- Mensaje de éxito -->
      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>

      <!-- Mensaje de error -->
      <div v-if="errorMessage" class="alert alert-error">
        {{ errorMessage }}
      </div>

      <form @submit.prevent="handleSaveProfile" class="profile-form">
        <div class="form-group">
          <label for="username">Nombre</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="Tu nombre"
            required
          />
        </div>

        <div class="form-group">
          <label for="apellido">Apellido</label>
          <input
            id="apellido"
            v-model="formData.apellido"
            type="text"
            placeholder="Tu apellido"
            required
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            :value="formData.email"
            type="email"
            disabled
            placeholder="Tu email"
          />
          <small>El email no puede ser modificado</small>
        </div>

        <div class="form-group">
          <label for="dni">DNI</label>
          <input
            id="dni"
            v-model="formData.dni"
            type="text"
            placeholder="Tu DNI"
            required
          />
        </div>

        <div class="form-group">
          <label for="telefono">Teléfono</label>
          <input
            id="telefono"
            v-model="formData.telefono"
            type="tel"
            placeholder="Tu teléfono"
            required
          />
        </div>

        <button type="submit" class="btn-submit" :disabled="isLoading">
          {{ isLoading ? 'Guardando...' : 'Guardar cambios' }}
        </button>
      </form>
    </section>

    <!-- Botón de eliminación de cuenta -->
    <section class="profile-section">
      <h2>Cambiar contraseña</h2>

      <div v-if="passwordSuccessMessage" class="alert alert-success">
        {{ passwordSuccessMessage }}
      </div>

      <div v-if="passwordErrorMessage" class="alert alert-error">
        {{ passwordErrorMessage }}
      </div>

      <form @submit.prevent="handleChangePassword" class="profile-form">
        <div class="form-group">
          <label for="current-password">Contraseña actual</label>
          <input
            id="current-password"
            v-model="passwordForm.current_password"
            type="password"
            autocomplete="current-password"
          />
        </div>

        <div class="form-group">
          <label for="new-password">Nueva contraseña</label>
          <input
            id="new-password"
            v-model="passwordForm.new_password"
            type="password"
            autocomplete="new-password"
          />
        </div>

        <div class="form-group">
          <label for="confirm-password">Confirmación de nueva contraseña</label>
          <input
            id="confirm-password"
            v-model="passwordForm.confirm_password"
            type="password"
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="btn-submit" :disabled="isChangingPassword">
          {{ isChangingPassword ? 'Cambiando...' : 'Cambiar contraseña' }}
        </button>
      </form>
    </section>

    <div class="delete-action">
      <button type="button" class="btn-delete" @click="openDeleteConfirm">
        Eliminar Usuario
      </button>
      <!-- Mensaje de error al eliminar -->
      <div v-if="deleteErrorMessage" class="alert alert-error delete-error">
        {{ deleteErrorMessage }}
      </div>
    </div>

    <!-- Modal de confirmación de eliminación -->
    <div v-if="showDeleteConfirm" class="delete-confirm-overlay">
      <div class="confirm-box">
        <p>¿Está seguro que desea eliminar su cuenta? Esta acción no se puede deshacer.</p>
        <div class="buttons">
          <button @click="confirmDelete" class="btn-danger" :disabled="isDeleting">
            {{ isDeleting ? 'Eliminando...' : 'Confirmar' }}
          </button>
          <button @click="cancelDelete" class="btn-secondary" :disabled="isDeleting">Cancelar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCurrentUser, updateProfile, changePassword, deleteAccount, logout } from '../../services/api'
import { roleHelpers } from '../../utils/roleHelpers'
import { useRouter } from 'vue-router'

const router = useRouter()
// Estado reactivo
const formData = ref({
  username: '',
  apellido: '',
  email: '',
    dni: '',
  telefono: ''
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const isLoading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const isChangingPassword = ref(false)
const passwordSuccessMessage = ref('')
const passwordErrorMessage = ref('')
const deleteErrorMessage = ref('')
const showDeleteConfirm = ref(false)
const isDeleting = ref(false)

// Cargar datos del usuario actual
onMounted(async () => {
  try {
    const response = await getCurrentUser()
    const user = response.data.user
    formData.value = {
      username: user.username || '',
      apellido: user.apellido || '',
      email: user.email || '',
      dni: user.dni || '',
      telefono: user.telefono || ''
    }
  } catch (err) {
    errorMessage.value = 'No se pudo cargar los datos del perfil'
  }
})

// Guardar cambios del perfil
const handleSaveProfile = async () => {
  // Limpiar mensajes previos
  successMessage.value = ''
  errorMessage.value = ''

  // Validar que los campos obligatorios no estén vacíos
  if (!formData.value.username.trim()) {
    errorMessage.value = 'El nombre es obligatorio'
    return
  }

  if (!formData.value.apellido.trim()) {
    errorMessage.value = 'El apellido es obligatorio'
    return
  }

  if (!formData.value.dni.trim()) {
    errorMessage.value = 'El DNI es obligatorio'
    return
  }

  if (!formData.value.telefono.trim()) {
    errorMessage.value = 'El teléfono es obligatorio'
    return
  }

  isLoading.value = true

  try {
    await updateProfile({
      username: formData.value.username.trim(),
      apellido: formData.value.apellido.trim(),
      telefono: formData.value.telefono.trim(),
      dni: formData.value.dni.trim()
    })
    successMessage.value = 'Perfil actualizado correctamente'
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error al actualizar el perfil'
  } finally {
    isLoading.value = false
  }
}

const handleChangePassword = async () => {
  passwordSuccessMessage.value = ''
  passwordErrorMessage.value = ''

  isChangingPassword.value = true

  try {
    await changePassword({
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password,
      confirm_password: passwordForm.value.confirm_password
    })
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
    passwordSuccessMessage.value = 'La contraseña fue actualizada correctamente.'
  } catch (err) {
    passwordErrorMessage.value = err.response?.data?.error || 'Error al actualizar la contraseña'
  } finally {
    isChangingPassword.value = false
  }
}

const openDeleteConfirm = () => {
  deleteErrorMessage.value = ''
  showDeleteConfirm.value = true
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
}

const confirmDelete = async () => {
  isDeleting.value = true
  try {
    // Ejecuta la función del endpoint para eliminar la cuenta y cierra sesión
    await deleteAccount()
    await logout()
    showDeleteConfirm.value = false
    router.push('/login')
  } catch (err) {
    deleteErrorMessage.value = err.response?.data?.error || 'Error al eliminar la cuenta'
    showDeleteConfirm.value = false
  } finally {
    isDeleting.value = false
  }
}
</script>

<style scoped>
.configuracion-view {
  padding: 24px;
  min-height: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.subtitle {
  color: #6b5d7b;
  margin-bottom: 2rem;
}

/* Sección de Perfil */
.profile-section {
  background: #f8f7fa;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 2rem;
  border: 1px solid #e8e4f0;
}

.profile-section h2 {
  font-size: 1.3rem;
  margin-bottom: 1.5rem;
  color: #582c57;
}

/* Formulario */
.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #582c57;
  font-size: 0.9rem;
}

.form-group input {
  padding: 10px 12px;
  border: 1px solid #d8d0e0;
  border-radius: 4px;
  font-size: 0.95rem;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #582c57;
  box-shadow: 0 0 0 3px rgba(88, 44, 87, 0.1);
}

.form-group input:disabled {
  background-color: #efefef;
  cursor: not-allowed;
}

.form-group small {
  color: #999;
  font-size: 0.8rem;
}

/* Alertas */
.alert {
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.95rem;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.alert-success {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

.alert-error {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

/* Botón Submit */
.btn-submit {
  padding: 12px 20px;
  background-color: #582c57;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 0.5rem;
}

.btn-submit:hover:not(:disabled) {
  background-color: #6b3a6f;
}

.btn-submit:disabled {
  background-color: #bbb;
  cursor: not-allowed;
}

/* Otras opciones */
.config-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  max-width: 760px;
}

.small-button {
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 6px;
  min-width: 220px;
  display: inline-flex;
  justify-content: center;
}

/* === ESTILOS PARA LA ELIMINACIÓN DE CUENTA === */
.delete-action {
  margin-top: 2rem;
  text-align: left;
}

.btn-delete {
  padding: 10px 16px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-delete:hover {
  background-color: #c82333;
}

.delete-error {
  margin-top: 1rem;
}

/* Modal de confirmación */
.delete-confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.confirm-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  text-align: center;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.confirm-box p {
  margin-bottom: 20px;
  font-size: 1.1rem;
  color: #333;
}

.buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c82333;
}

.btn-secondary {
  background: #f5e6f5;
  color: #572c57;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e8dce8;
}

.btn-danger:disabled,
.btn-secondary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Media Queries */
@media (max-width: 768px) {
  .configuracion-view {
    padding: 16px;
  }

  .profile-section {
    padding: 16px;
  }

  .profile-section h2 {
    font-size: 1.1rem;
  }

  .form-group input {
    padding: 8px 10px;
    font-size: 0.9rem;
  }

  .btn-submit {
    padding: 10px 16px;
    font-size: 0.9rem;
  }
}
</style>
