<template>
  <div class="notification-settings-view view">
    <div class="page-header">
      <h1>Configuración de notificación</h1>
      <p>Configurar el mensaje de notificación para cuando se cancela una clase.</p>
    </div>

    <div>
      <form class="notification-form" @submit.prevent="onSubmit">
        <div class="field">
          <textarea
            id="notification-message"
            v-model="message"
            rows="6"
            placeholder="Ingrese el texto que se enviará cuando se cancele una clase"
          ></textarea>
        </div>

        <div v-if="errorMessage" class="msg error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="msg success">{{ successMessage }}</div>

        <button type="submit" class="small-button" :disabled="loading">
          {{ loading ? 'Guardando...' : 'Configurar notificación' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNotificationConfig, saveNotificationConfig } from '../../services/api'

const message = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(false)

async function loadNotificationConfig() {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await getNotificationConfig()
    message.value = response.data.message || ''
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'No se pudo cargar la configuración de notificación.'
  }
}

async function onSubmit() {
  errorMessage.value = ''
  successMessage.value = ''
  const trimmedMessage = message.value.trim()

  if (!trimmedMessage) {
    errorMessage.value = 'El campo del mensaje es obligatorio.'
    return
  }

  loading.value = true
  try {
    const response = await saveNotificationConfig(trimmedMessage)
    successMessage.value = response.data.message || 'Notificación configurada correctamente.'
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'No se pudo guardar el mensaje de notificación.'
  } finally {
    loading.value = false
  }
}

onMounted(loadNotificationConfig)
</script>

<style scoped>
.notification-settings-view {
  padding: 24px;
  max-width: 840px;
}

.page-header h1 {
  margin: 0;
  font-size: 2rem;
}

.page-header p {
  margin: 0.75rem 0 2rem;
  color: #d1d5db;
}

.notification-card {
  padding: 1.5rem;
}

.notification-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.field label {
  font-weight: 700;
  color: #f5f5f5;
}

.field textarea {
  width: 100%;
  min-height: 170px;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: vertical;
  font-size: 1rem;
  font-family: inherit;
  color: #121212;
  background: #ffffff;
}

.field textarea:focus {
  outline: none;
  border-color: #9f5f91;
  box-shadow: 0 0 0 3px rgba(159, 95, 145, 0.12);
}

.msg {
  padding: 0.9rem 1rem;
  border-radius: 10px;
  font-size: 0.95rem;
  margin-bottom: 0;
}

.error {
  background: #fde2e6;
  color: #861d2c;
  border: 1px solid #f7c0c9;
}

.success {
  background: #e6f4ea;
  color: #166534;
  border: 1px solid #a7f3d0;
}

.small-button {
  align-self: flex-start;
  font-size: 14px;
  padding: 10px 14px;
  border-radius: 6px;
  min-width: 220px;
}

.small-button:hover:not(:disabled) {
  background: #f6ea98;
  color: #9f5f91;
}

.small-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.field label {
  font-weight: 700;
  color: #2f2f2f;
}

.field textarea {
  width: 100%;
  min-height: 170px;
  padding: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  resize: vertical;
  font-size: 1rem;
  font-family: inherit;
}

.field textarea:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
}

.msg {
  padding: 0.9rem 1rem;
  border-radius: 10px;
  font-size: 0.95rem;
  margin-bottom: 1rem;
}

.error {
  background: #fde2e6;
  color: #861d2c;
  border: 1px solid #f7c0c9;
}

.success {
  background: #e6f4ea;
  color: #166534;
  border: 1px solid #a7f3d0;
}

button.btn-primary {
  background: #7c3aed;
  color: white;
  border: none;
  padding: 0.95rem 1.4rem;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

button.btn-primary:hover:not(:disabled) {
  background: #6d28d9;
  transform: translateY(-1px);
}

button.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
