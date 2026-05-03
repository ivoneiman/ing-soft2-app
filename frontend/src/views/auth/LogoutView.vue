<template>
  <div class="logout-container">
    <p>Cerrando sesión...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { logout } from '../../services/api'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(async () => {
  try {
    await logout()
  } catch (e) {
    // ignore errors, still redirect
  }
  router.push('/login')
})
</script>

<style scoped>
.logout-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
  font-size: 1.2rem;
}
</style>
