<template>
  <div class="home-container">
    <h2>Bienvenido</h2>
    <div v-if="loading">Cargando usuario...</div>
    <div v-else-if="user">
      <p>Hola, {{ user.username }} ({{ user.email }})</p>
      <button @click="onLogout">Cerrar sesión</button>
    </div>
    <div v-else>
      <p>No hay usuario logueado.</p>
    </div>
  </div>
</template>

<script setup>
// Importamos ref y onMounted para manejar estado y ciclo de vida
import { ref, onMounted } from 'vue'
import { getCurrentUser, logout } from '../services/api'
import { useRouter } from 'vue-router'

const user = ref(null)
const loading = ref(true)
const router = useRouter()

// Al montar el componente, pedimos el usuario actual
onMounted(async () => {
  try {
    const response = await getCurrentUser()
    user.value = response.data.user
  } catch (err) {
    // Si no hay sesión, redirigimos a login
    router.push('/login')
  } finally {
    loading.value = false
  }
})

// Función para cerrar sesión
async function onLogout() {
  await logout()
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #eee;
  border-radius: 8px;
}
</style>
