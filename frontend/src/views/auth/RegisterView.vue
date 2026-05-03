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
// Importamos `ref` para crear variables reactivas (similares a state en React)
import { ref } from 'vue'
// `register` es una función que envía una petición POST a la API backend
import { register } from '../../services/api'
// `RouterLink` permite crear enlaces internos sin recargar la página (SPA navigation)
import { RouterLink } from 'vue-router'

// Variables reactivas que almacenan los valores del formulario y el estado UI
const username = ref('')   // nombre de usuario ingresado
const email = ref('')       // email ingresado
const password = ref('')    // contraseña ingresada
const error = ref('')       // mensaje de error a mostrar
const success = ref('')     // mensaje de éxito a mostrar
const loading = ref(false)  // indica si la petición está en curso

// Función que se ejecuta al enviar el formulario
// Maneja el envío del formulario
async function onSubmit() {
  // Reiniciamos mensajes de estado
  error.value = ''
  success.value = ''
  loading.value = true // muestra spinner / deshabilita botón
  try {
    // Llamamos a la API de registro con los datos del formulario
    await register({ username: username.value, email: email.value, password: password.value })
    // Si la petición es exitosa, informamos al usuario y limpiamos los campos
    success.value = 'Usuario creado correctamente. Ya puedes iniciar sesión.'
    username.value = ''
    email.value = ''
    password.value = ''
  } catch (err) {
    // En caso de error, mostramos el mensaje del backend o un fallback genérico
    error.value = err.response?.data?.error || 'Error al registrar usuario'
  } finally {
    loading.value = false // vuelve a habilitar el botón
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
