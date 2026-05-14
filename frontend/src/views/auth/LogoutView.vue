<template>
  <div class="logout-container">
    <!-- Confirmación antes de cerrar sesión -->
    <div v-if="showConfirm" class="confirm-box">
      <p>¿Está seguro que desea cerrar sesión?</p>
      <div class="buttons">
        <button @click="confirmLogout" :disabled="loading">Sí, cerrar sesión</button>
        <button @click="cancelLogout" :disabled="loading">No, volver</button>
      </div>
    </div>
    <!-- Mensaje mientras se procesa el logout -->
    <div v-else class="processing">
      <p>Cerrando sesión...</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { logout } from '../../services/api'
import { useRouter } from 'vue-router'

const router = useRouter()
const showConfirm = ref(true) // muestra la ventana de confirmación
const loading = ref(false)

/**
 * Ejecuta el logout y redirige al login.
 */
async function performLogout() {
  loading.value = true
  try {
    await logout()
  } catch (e) {
    // Ignorar errores de logout, seguimos redirigiendo
  } finally {
    router.push('/login')
  }
}

function confirmLogout() {
  showConfirm.value = false
  performLogout()
}

function cancelLogout() {
  // Volver a la página anterior o a home
  router.back()
}
</script>

<style scoped>
.logout-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
  font-size: 1.2rem;
  flex-direction: column;
}
.confirm-box {
  text-align: center;
}
.buttons {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
}
.buttons button {
  padding: 0.5rem 1rem;
}
.processing {
  text-align: center;
}
</style>
