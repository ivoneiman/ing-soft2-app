<!--
  Vista de registro de usuarios.
  Contiene un formulario que captura nombre de usuario, email y contraseña,
  y envía esos datos a la API backend mediante la función `register`.
  El componente muestra mensajes de error o éxito y permite navegar a la vista de login.
-->
<template>
  <div class="register-container">
    <h2>Crear cuenta</h2>
    <!-- El modificador .prevent evita que el formulario recargue la página al enviarse -->
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
import { ref } from 'vue'
import { register } from '../../services/api'
import { RouterLink } from 'vue-router'

// Variables reactivas que almacenan los valores del formulario y el estado UI
const username = ref('')   // nombre de usuario ingresado
const email = ref('')       // email ingresado
const password = ref('')    // contraseña ingresada
const error = ref('')       // mensaje de error a mostrar
const success = ref('')     // mensaje de éxito a mostrar
const loading = ref(false)  // indica si la petición está en curso

/**
 * Maneja el envío del formulario de registro.
 * Se añaden validaciones simples para mejorar la claridad de los mensajes de error.
 */
async function onSubmit() {
  // Reiniciamos mensajes de estado
  error.value = ''
  success.value = ''

  // Validaciones básicas de campos obligatorios
  if (!username.value.trim() || !email.value.trim() || !password.value.trim()) {
    error.value = 'Debe completar todos los campos'
    return
  }
  // Validación de longitud mínima de contraseña
  if (password.value.length < 6) {
    error.value = 'La contraseña debe tener al menos 6 caracteres'
    return
  }

  loading.value = true // muestra spinner / deshabilita botón
  try {
    await register({ username: username.value, email: email.value, password: password.value })
    success.value = 'Usuario creado correctamente. Ya puedes iniciar sesión.'
    username.value = ''
    email.value = ''
    password.value = ''
  } catch (err) {
    if (err.response?.data?.error) {
      // Mensaje específico del backend (p.ej., email ya registrado)
      error.value = err.response.data.error
    } else if (!err.response) {
      error.value = 'No se pudo conectar con el servidor'
    } else {
      error.value = 'Error al registrar usuario'
    }
  } finally {
    loading.value = false
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