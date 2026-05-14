<!--
  Vista de inicio de sesión.
  Presenta un formulario que solicita email y contraseña, llama a la API de login
  y, si la autenticación es exitosa, redirige al usuario a la página principal.
  También muestra un enlace a la vista de registro.
-->
<template>
  <div class="login-container">
    <h2>Iniciar sesión</h2>
    <!-- El modificador .prevent evita que el formulario recargue la página al enviarse -->
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
// Importamos `ref` para crear variables reactivas (similar a state en React)
import { ref } from 'vue'
// `login` envía una petición POST a la API backend con email y contraseña
import { login } from '../../services/api'
// `RouterLink` permite crear enlaces internos sin recargar la página (SPA navigation)
import { RouterLink } from 'vue-router'

// Variables reactivas que almacenan los valores del formulario y el estado UI
const email = ref('')      // email ingresado por el usuario
const password = ref('')   // contraseña ingresada
const error = ref('')      // mensaje de error a mostrar
const loading = ref(false) // indica si la petición está en curso

// Función que se ejecuta al enviar el formulario
// Maneja el envío del formulario de login
async function onSubmit() {
  // Reiniciamos el mensaje de error y marcamos carga
  error.value = ''
  loading.value = true
  try {
    // Llamamos a la API de login con los datos del formulario
    await login({ email: email.value, password: password.value })
    // Si la autenticación es exitosa, redirigimos al home (puedes cambiar la ruta)
    window.location.href = '/' // O usa router.push si tienes rutas protegidas
  } catch (err) {
    // En caso de error, mostramos el mensaje del backend o un fallback genérico
    error.value = err.response?.data?.error || 'Error al iniciar sesión'
  } finally {
    loading.value = false // vuelve a habilitar el botón
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
  background: white;
}

.error {
  color: red;
  margin-top: 1rem;
}

.link-text {
  margin-top: 1rem;
  text-align: center;
}

/* ==========================================
   MEDIA QUERIES - TABLET (1024px)
   ========================================== */

@media (max-width: 1024px) {
  .login-container {
    max-width: 350px;
    margin: 1.5rem auto;
    padding: 1.5rem;
  }
}

/* ==========================================
   MEDIA QUERIES - MOBILE (768px)
   ========================================== */

@media (max-width: 768px) {
  .login-container {
    max-width: 100%;
    margin: 1rem;
    padding: 1.5rem;
    border: none;
    border-radius: 12px;
  }
}

/* ==========================================
   MEDIA QUERIES - PEQUEÑOS MÓVILES (480px)
   ========================================== */

@media (max-width: 480px) {
  .login-container {
    margin: 0.5rem;
    padding: 1rem;
  }
}
</style>
