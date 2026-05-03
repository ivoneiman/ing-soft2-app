<template>
  <nav class="default-navbar">
    <!-- Logo -->
    <router-link to="/" class="logo-link">
      <img src="/logo-con-aura.png" alt="Logo" class="logo" />
    </router-link>

    <!-- Centro -->
    <div class="center-menu">
      <router-link to="/" class="nav-item">Home</router-link>
      <router-link to="/actividades" class="nav-item">Actividades</router-link>
      <router-link to="/sobre-nosotros" class="nav-item">Sobre Nosotros</router-link>

      <router-link
        v-if="!authStore.isLoggedIn"
        to="/login"
        class="nav-item"
      >
        Iniciar Sesión
      </router-link>

      <!-- Dropdown perfil -->
      <div v-else class="dropdown" ref="dropdownRef">
        <button class="dropdown-header" @click="toggleDropdown">
          Perfil
          <span class="arrow">
            {{ isDropdownOpen ? '▲' : '▼' }}
          </span>
        </button>

        <div v-if="isDropdownOpen" class="dropdown-container">
          <router-link to="/configuracion" @click="closeDropdown">
            Configuración
          </router-link>
          <router-link to="/pagos" @click="closeDropdown">
            Pagos
          </router-link>
          <router-link to="/reportes" @click="closeDropdown">
            Reportes
          </router-link>
          <a href="#" @click.prevent="handleLogout">
            Cerrar sesión
          </a>
        </div>
      </div>
    </div>

    <!-- Derecha -->
    <div class="right-section" v-if="authStore.isLoggedIn">
      <span class="present-text">PASAR <br /> PRESENTE</span>
      <img src="/codigo-qr.png" alt="QR" class="qr-image" />
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { authStore } from '../services/authStore'
import { useRouter } from 'vue-router'

const router = useRouter()

const isDropdownOpen = ref(false)
const dropdownRef = ref(null)

function toggleDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
}

function closeDropdown() {
  isDropdownOpen.value = false
}

onClickOutside(dropdownRef, () => {
  closeDropdown()
})

async function handleLogout() {
  closeDropdown()
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* NAVBAR */
.default-navbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #ddd;
  background: transparent;
}

/* LOGO */
.logo {
  height: 120px;
  flex-shrink: 0;
}

/* MENÚ CENTRAL */
.center-menu {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  justify-content: center;
}

/* LINKS */
.nav-item {
  text-decoration: none;
  color: #ffffff;
  font-weight: 500;
}

.nav-item:hover {
  color: #e26972;
}

/* DROPDOWN */
.dropdown {
  position: relative;
}

/* BOTÓN PERFIL */
.dropdown-header {
  background: none;
  border: none;
  font-weight: 600;
  color: #e26972;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* FLECHA */
.arrow {
  font-size: 12px;
}

/* MENÚ DESPLEGABLE */
.dropdown-container {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: #f6ea98;
  border-radius: 8px;
  min-width: 180px;
  box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.2);
  margin-top: 8px;
  z-index: 100;
  overflow: hidden;
}

/* ITEMS */
.dropdown-container a {
  display: block;
  padding: 10px 14px;
  text-decoration: none;
  color: #8a4f8a;
}

/* HOVER */
.dropdown-container a:hover {
  color: #572c57;
}

/* DERECHA */
.right-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.present-text {
  font-weight: 600;
  font-size: 20px;
  font-family: Poppins, sans-serif;
  text-align: right;
}

.qr-image {
  height: 80px;
  border-radius: 15px;
}
</style>