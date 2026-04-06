<template>
  <div class="login-container">
    <h2>Iniciar sesión</h2>
    <form @submit.prevent="onSubmit">
      <div>
        <label for="email">Email:</label>
        <input id="email" v-model="email" type="email" required />
      </div>
      <div>
        <label for="password">Contraseña:</label>
        <input id="password" v-model="password" type="password" required />
      </div>
      <button type="submit" :disabled="loading">Ingresar</button>
      <div v-if="error" class="error">{{ error }}</div>
    </form>
    <!-- Enlace a la vista de registro. RouterLink permite navegar sin recargar la página. -->
    <p class="link-text">
      ¿No tienes cuenta?
      <RouterLink to="/register">Crear cuenta</RouterLink>
    </p>
  </div>
</template>

<script setup>
// Importamos ref para variables reactivas y la función de login de la API
import { ref } from 'vue'
import { login } from '../services/api'
// Importamos RouterLink para usar enlaces internos de Vue Router
import { RouterLink } from 'vue-router'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

// Función que se ejecuta al enviar el formulario
async function onSubmit() {
  error.value = '' // Limpiamos errores anteriores
  loading.value = true // Mostramos estado de carga
  try {
    // Llamamos a la API de login con los datos del formulario
    await login({ email: email.value, password: password.value })
    // Si el login es exitoso, redirigimos al home (puedes cambiar esto luego)
    window.location.href = '/' // O usa router.push si tienes rutas protegidas
  } catch (err) {
    // Si hay error, mostramos el mensaje recibido del backend o uno genérico
    error.value = err.response?.data?.error || 'Error al iniciar sesión'
  } finally {
    loading.value = false // Ocultamos el estado de carga
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #eee;
  border-radius: 8px;
}
.error {
  color: red;
  margin-top: 1rem;
}
.link-text {
  margin-top: 1rem;
  text-align: center;
}
</style>
