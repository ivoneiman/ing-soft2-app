<template>
  <div class="card">
    <h2 style="margin-bottom: 20px;">Crear cuenta</h2>

    <p v-if="authStore.error" class="error">{{ authStore.error }}</p>

    <input v-model="username" type="text" placeholder="Username" />
    <input v-model="email" type="email" placeholder="Email" />
    <input v-model="password" type="password" placeholder="Contraseña" />

    <button @click="handleRegister" :disabled="authStore.loading" style="width: 100%;">
      {{ authStore.loading ? 'Creando cuenta...' : 'Registrarse' }}
    </button>

    <p style="margin-top: 16px; font-size: 14px; text-align: center;">
      ¿Ya tenés cuenta?
      <router-link to="/login">Iniciá sesión</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../services/authStore'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')

async function handleRegister() {
  const ok = await authStore.register(username.value, email.value, password.value)
  if (ok) router.push('/dashboard')
}
</script>
