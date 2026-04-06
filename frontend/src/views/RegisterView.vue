<template>
  <div class="register-container">
    <h2>Crear cuenta</h2>
    <form @submit.prevent="onSubmit">
      <div>
        <label for="username">Usuario:</label>
        <input id="username" v-model="username" type="text" required />
      </div>
      <div>
        <label for="email">Email:</label>
        <input id="email" v-model="email" type="email" required />
      </div>
      <div>
        <label for="password">Contraseña:</label>
        <input id="password" v-model="password" type="password" required />
      </div>
      <button type="submit" :disabled="loading">Registrarse</button>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="success" class="success">{{ success }}</div>
    </form>
    <!-- Enlace a la vista de login. RouterLink permite navegar sin recargar la página. -->
    <p class="link-text">
      ¿Ya tienes cuenta?
      <RouterLink to="/login">Iniciar sesión</RouterLink>
    </p>
  </div>
</template>

<script setup>
// Importamos ref para variables reactivas y la función de registro de la API
import { ref } from 'vue'
import { register } from '../services/api'
// Importamos RouterLink para usar enlaces internos de Vue Router
import { RouterLink } from 'vue-router'

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

// Función que se ejecuta al enviar el formulario
async function onSubmit() {
  error.value = '' // Limpiamos errores anteriores
  success.value = '' // Limpiamos mensajes de éxito anteriores
  loading.value = true // Mostramos estado de carga
  try {
    // Llamamos a la API de registro con los datos del formulario
    await register({ username: username.value, email: email.value, password: password.value })
    // Si el registro es exitoso, mostramos mensaje y limpiamos campos
    success.value = 'Usuario creado correctamente. Ya puedes iniciar sesión.'
    username.value = ''
    email.value = ''
    password.value = ''
  } catch (err) {
    // Si hay error, mostramos el mensaje recibido del backend o uno genérico
    error.value = err.response?.data?.error || 'Error al registrar usuario'
  } finally {
    loading.value = false // Ocultamos el estado de carga
  }
}
</script>

<style scoped>
.register-container {
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
.success {
  color: green;
  margin-top: 1rem;
}
.link-text {
  margin-top: 1rem;
  text-align: center;
}
</style>
