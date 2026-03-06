<template>
  <div class="card">
    <h2 style="margin-bottom: 20px;">Iniciar sesión</h2>

    <p v-if="authStore.error" class="error">{{ authStore.error }}</p>

    <input v-model="email" type="email" placeholder="Email" />
    <input v-model="password" type="password" placeholder="Contraseña" @keyup.enter="handleLogin" />

    <button @click="handleLogin" :disabled="authStore.loading" style="width: 100%;">
      {{ authStore.loading ? 'Cargando...' : 'Ingresar' }}
    </button>

    <p style="margin-top: 16px; font-size: 14px; text-align: center;">
      ¿No tenés cuenta?
      <router-link to="/register">Registrate</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../services/authStore'

const router = useRouter()
const email = ref('')
const password = ref('')

async function handleLogin() {
  const ok = await authStore.login(email.value, password.value)
  if (ok) router.push('/dashboard')
}
</script>
