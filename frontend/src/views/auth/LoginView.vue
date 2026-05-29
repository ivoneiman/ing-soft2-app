<!--
  Vista de inicio de sesión.
  Presenta un formulario que solicita email y contraseña, llama a la API de login
  y, si la autenticación es exitosa, redirige al usuario a la página principal.
  También muestra un enlace a la vista de registro.
-->
<template>
  <div class="login-container">
    <h2>Iniciar sesión</h2>
    <div class="mode-buttons">
      <button type="button" class="mode-button" :class="{ active: mode === 'password' }" @click="setMode('password')">
        Login normal
      </button>
      <button type="button" class="mode-button" :class="{ active: mode === 'admin-code' }" @click="setMode('admin-code')">
        Administrador por código
      </button>
    </div>

    <form @submit.prevent="onSubmit">
      <div>
        <label for="email">Email:</label>
        <input id="email" v-model="email" type="email" :disabled="mode === 'admin-code' && codeSent" required />
      </div>

      <div v-if="mode === 'password' || mode === 'admin-code'">
        <label for="password">Contraseña:</label>
        <input id="password" v-model="password" type="password" :disabled="mode === 'admin-code' && codeSent" required />
      </div>

      <div v-if="mode === 'admin-code' && codeSent">
        <label for="code">Código de verificación:</label>
        <input id="code" v-model="code" type="text" maxlength="6" required />
      </div>

      <button type="submit" :disabled="loading">
        {{ mode === 'admin-code' ? (codeSent ? 'Verificar código' : 'Recibir código') : 'Ingresar' }}
      </button>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="info" class="info">{{ info }}</div>
    </form>
    <!-- Enlace a la vista de registro.-->
    <p class="link-text" v-if="mode === 'password'">
      ¿No tienes cuenta?
      <RouterLink to="/register">Crear cuenta</RouterLink>
    </p>
  </div>
</template>

<script setup>

import { ref } from 'vue'
import { authStore } from '../../services/authStore'
import { RouterLink, useRoute, useRouter } from 'vue-router'
// Variables reactivas para manejar el estado del formulario y el estado UI.
const route = useRoute()
const router = useRouter()
const mode = ref('password')
const email = ref('') //email ingresado por el usuario
const password = ref('')// contraseña ingresada por el usuario
const code = ref('')
const error = ref('')// mensaje de error a mostrar al usuario
const info = ref('')
const loading = ref(false)//indica si peticion está en curso
const codeSent = ref(false)

function redirectAfterLogin() {
  router.push(route.query.redirect || '/')
}

function setMode(newMode) {
  mode.value = newMode
  error.value = ''
  info.value = ''
  password.value = ''
  code.value = ''
  codeSent.value = false
}

async function onSubmit() {
  // Reiniciamos el mensaje de error y marcamos carga
  error.value = ''
  info.value = ''
  //validación de campos obligatorios
  if (!email.value.trim()) {
    error.value = 'Debe completar el email'
    return
  }

  loading.value = true
  try {
    if (mode.value === 'admin-code') {
      if (!codeSent.value) {
        if (!password.value.trim()) {
          error.value = 'Debe completar la contraseña'
          return
        }
        const ok = await authStore.adminLoginRequest(email.value, password.value)
        if (ok) {
          info.value = 'Se envió un código al email. Ingresalo a continuación.'
          codeSent.value = true
        } else {
          error.value = authStore.error || 'No se pudo solicitar el código'
        }
      } else {
        if (!code.value.trim()) {
          error.value = 'Debe completar el código'
          return
        }
        const ok = await authStore.adminLoginVerify(email.value, code.value.trim())
        if (ok) {
          redirectAfterLogin()
        } else {
          error.value = authStore.error || 'Código incorrecto'
        }
      }
    } else {
      if (!password.value.trim()) {
        error.value = 'Debe completar la contraseña'
        return
      }
      const ok = await authStore.login(email.value, password.value)
      if (ok) {
        redirectAfterLogin()
      } else {
        error.value = authStore.error || 'Email o contraseña incorrectos'
      }
    }
  } finally {
    loading.value = false
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

  .info {
    color: #0a6e10;
    margin-top: 1rem;
  }

  .mode-buttons {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .mode-button {
    flex: 1;
    padding: 0.75rem 1rem;
    border: 1px solid #ccc;
    background: white;
    cursor: pointer;
    border-radius: 6px;
  }

  .mode-button.active {
    border-color: #2f8fe2;
    background: #eff6ff;
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
