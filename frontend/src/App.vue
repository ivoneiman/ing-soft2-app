<template>
  <div id="app">
    <nav v-if="authStore.isLoggedIn">
      <span>👤 {{ authStore.user.username }}</span>
      <button @click="handleLogout">Cerrar sesión</button>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { authStore } from './services/authStore'
import { useRouter } from 'vue-router'

const router = useRouter()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: sans-serif; background: #f5f5f5; color: #333; }
nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #ddd;
}
button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #4f46e5;
  color: white;
  cursor: pointer;
  font-size: 14px;
}
button:hover { background: #4338ca; }
button:disabled { background: #9ca3af; cursor: not-allowed; }
input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 12px;
}
.error { color: #dc2626; font-size: 14px; margin-bottom: 12px; }
.card {
  background: white;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  max-width: 420px;
  margin: 60px auto;
}
</style>
