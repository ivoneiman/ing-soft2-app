<template>
  <nav :class="['default-navbar', { 'navbar-home': route.path === '/' }]">
    <!-- Logo -->
    <router-link to="/" class="logo-link">
      <img src="/logo-con-aura.png" alt="Logo" class="logo" />
    </router-link>

    <!-- Botón Hamburguesa (solo mobile) -->
    <button class="hamburger-btn" @click="toggleMobileMenu" aria-label="Abrir menú">
      <span :class="{ active: isMobileMenuOpen }"></span>
      <span :class="{ active: isMobileMenuOpen }"></span>
      <span :class="{ active: isMobileMenuOpen }"></span>
    </button>

    <!-- Centro (se oculta en mobile, muestra en desktop) -->
    <div class="center-menu" :class="{ active: isMobileMenuOpen }">
      <router-link to="/" class="nav-item" @click="closeMobileMenu">Home</router-link>
      <!-- Dashboard para admin y employee -->
      <router-link v-if="authStore.isLoggedIn && (roleHelpers.isAdmin() || roleHelpers.isEmployee())" to="/dashboard" class="nav-item" @click="closeMobileMenu">Dashboard</router-link>
      <!-- Solo clientes pueden ver Actividades -->
      <router-link v-if="!authStore.isLoggedIn || roleHelpers.isClient()" to="/actividades" class="nav-item" @click="closeMobileMenu">Actividades</router-link>
      <router-link to="/sobre-nosotros" class="nav-item" @click="closeMobileMenu">Sobre Nosotros</router-link>

      <!-- Si no está autenticado: mostrar Login y Registro -->
      <router-link
        v-if="!authStore.isLoggedIn"
        to="/login"
        class="nav-item"
        @click="closeMobileMenu"
      >
        Iniciar Sesión
      </router-link>
      <router-link
        v-if="!authStore.isLoggedIn"
        to="/register"
        class="nav-item"
        @click="closeMobileMenu"
      >
        Registro
      </router-link>

      <!-- Si está autenticado: mostrar opciones según rol -->
      <div v-if="authStore.isLoggedIn" class="auth-menu">
        <!-- CLIENT: Mi QR -->
        <router-link v-if="roleHelpers.isClient()" to="/mi-qr" class="nav-item" @click="closeMobileMenu">
          Mi QR
        </router-link>
        <div v-if="roleHelpers.isClient()" class="dropdown" ref="paymentsDropdownRef">
          <button
            class="dropdown-header"
            type="button"
            :aria-expanded="isPaymentsDropdownOpen"
            aria-haspopup="true"
            @click="togglePaymentsDropdown"
          >
            Pagos
            <span class="arrow">
              {{ isPaymentsDropdownOpen ? '▲' : '▼' }}
            </span>
          </button>

          <div v-if="isPaymentsDropdownOpen" class="dropdown-container">
            <router-link to="/pagos?tab=pending" @click="handlePaymentsDropdownClick">
              Inscripciones pendientes
            </router-link>
            <router-link to="/pagos?tab=history" @click="handlePaymentsDropdownClick">
              Historial de pagos
            </router-link>
          </div>
        </div>

        <!-- Dropdown administrativo -->
        <div v-if="roleHelpers.isAdmin() || roleHelpers.isEmployee()" class="dropdown" ref="adminDropdownRef">
          <button
            class="dropdown-header"
            type="button"
            :aria-expanded="isAdminDropdownOpen"
            aria-haspopup="true"
            @click="toggleAdminDropdown"
          >
            Administración
            <span class="arrow">
              {{ isAdminDropdownOpen ? '▲' : '▼' }}
            </span>
          </button>

          <div v-if="isAdminDropdownOpen" class="dropdown-container">
            <router-link to="/crear-clase" @click="handleAdminDropdownClick">
              Crear clases
            </router-link>
            <router-link to="/crear-usuario" @click="handleAdminDropdownClick">
              Crear Usuario
            </router-link>
            <router-link to="/pagos" @click="handleAdminDropdownClick">
              Pagos
            </router-link>
            <router-link to="/dashboard" @click="handleAdminDropdownClick">
              Dashboard
            </router-link>
            <router-link v-if="roleHelpers.isEmployee()" to="/pasar-asistencia" @click="handleAdminDropdownClick">
              Pasar Asistencia
            </router-link>
            <router-link v-if="roleHelpers.isAdmin()" to="/configuracion" @click="handleAdminDropdownClick">
              Configuración
            </router-link>
            <router-link v-if="roleHelpers.isAdmin()" to="/reportes" @click="handleAdminDropdownClick">
              Reportes
            </router-link>
            <router-link v-if="roleHelpers.isAdmin()" to="/admin/descuentos" @click="handleAdminDropdownClick">
              Gestión de descuentos
            </router-link>
          </div>
        </div>

        <a href="#" class="nav-item logout-link" @click.prevent="handleLogout">
          Cerrar sesión
        </a>
      </div>
    </div>

    <!-- Derecha: acceso rápido a QR/asistencia según rol (desktop) -->
    <router-link
      v-if="authStore.isLoggedIn && attendanceShortcutRoute"
      :to="attendanceShortcutRoute"
      class="right-section"
    >
      <span class="present-text">PASAR <br /> PRESENTE</span>
      <img src="/codigo-qr.png" alt="QR" class="qr-image" />
    </router-link>
  </nav>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { authStore } from '../../services/authStore'
import { roleHelpers } from '../../utils/roleHelpers'
import { useRouter, useRoute } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isAdminDropdownOpen = ref(false)
const isPaymentsDropdownOpen = ref(false)
const isMobileMenuOpen = ref(false)
const adminDropdownRef = ref(null)
const paymentsDropdownRef = ref(null)

const attendanceShortcutRoute = computed(() => {
  if (roleHelpers.isClient()) return '/mi-qr'
  if (roleHelpers.isEmployee()) return '/pasar-asistencia'
  return null
})

function toggleAdminDropdown() {
  isAdminDropdownOpen.value = !isAdminDropdownOpen.value
}

function closeAdminDropdown() {
  isAdminDropdownOpen.value = false
}

function togglePaymentsDropdown() {
  isPaymentsDropdownOpen.value = !isPaymentsDropdownOpen.value
}

function closePaymentsDropdown() {
  isPaymentsDropdownOpen.value = false
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
  closeAdminDropdown()
  closePaymentsDropdown()
}

function handleAdminDropdownClick() {
  closeAdminDropdown()
  closeMobileMenu()
}

function handlePaymentsDropdownClick() {
  closePaymentsDropdown()
  closeMobileMenu()
}

onClickOutside(adminDropdownRef, () => {
  closeAdminDropdown()
})

onClickOutside(paymentsDropdownRef, () => {
  closePaymentsDropdown()
})

function handleLogout() {
  closeMobileMenu()
  router.push('/logout')
}
</script>

<style scoped>
/* ==========================================
   NAVBAR RESPONSIVE - BASE DESKTOP
   ========================================== */

.default-navbar {
  position: relative;
  display: flex;
  align-items: center;
  padding: 16px 40px;
  background: #572c57;
  z-index: 1000;
  transition: all 0.3s ease;
  gap: 20px;
}

.navbar-home {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  background: rgba(87, 44, 87, 0.35);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* ==========================================
   LOGO
   ========================================== */

.logo {
  height: 130px;
  flex-shrink: 0;
  transition: height 0.3s ease;
}

.logo-link {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* ==========================================
   BOTÓN HAMBURGUESA (solo mobile)
   ========================================== */

.hamburger-btn {
  display: none;
  flex-direction: column;
  background: none;
  border: 0;
  color: #f6ea98;
  cursor: pointer;
  gap: 5px;
  padding: 8px;
  margin-left: auto;
}

.hamburger-btn span {
  width: 24px;
  height: 2px;
  background: currentColor;
  transition: all 0.3s ease;
  display: block;
}

/* Animación X cuando está abierto */
.hamburger-btn span.active:nth-child(1) {
  transform: rotate(45deg) translate(8px, 8px);
}

.hamburger-btn span.active:nth-child(2) {
  opacity: 0;
}

.hamburger-btn span.active:nth-child(3) {
  transform: rotate(-45deg) translate(8px, -8px);
}

/* ==========================================
   MENÚ CENTRAL
   ========================================== */

.center-menu {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  justify-content: center;
  background: transparent !important;
  flex-wrap: wrap;
}

.auth-menu {
  display: flex;
  align-items: center;
  gap: 16px;
  background: transparent !important;
}

/* ==========================================
   LINKS
   ========================================== */

.nav-item {
  text-decoration: none;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  transition: color 0.3s ease;
  white-space: nowrap;
}

.nav-item:hover,
.router-link-active.nav-item {
  color: #e26972;
}

.logout-link {
  color: #f6ea98;
}

/* ==========================================
   DROPDOWN ADMINISTRATIVO
   ========================================== */

.dropdown {
  position: relative;
  background: transparent !important;
}

.dropdown-header {
  background: transparent !important;
  border: 0;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: "Poppins", sans-serif;
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 1.5px;
  line-height: 18px;
  padding: 0;
  transition: color 0.3s ease;
  white-space: nowrap;
}

.dropdown-header:hover {
  color: #e26972;
}

.arrow {
  font-size: 12px;
}

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

.dropdown-container a {
  display: block;
  padding: 10px 14px;
  text-decoration: none;
  color: #8a4f8a;
  transition: color 0.3s ease;
}

.dropdown-container a:hover {
  color: #572c57;
}

/* ==========================================
   SECCIÓN DERECHA (QR)
   ========================================== */

.right-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
  background: transparent !important;
  flex-shrink: 0;
}

.present-text {
  font-weight: 600;
  font-size: 20px;
  font-family: Poppins, sans-serif;
  text-align: right;
  white-space: nowrap;
}

.qr-image {
  height: 80px;
  border-radius: 15px;
  flex-shrink: 0;
}

/* ==========================================
   MEDIA QUERIES - TABLET (768px)
   ========================================== */

@media (max-width: 1024px) {
  .default-navbar {
    padding: 16px 24px;
    gap: 16px;
  }

  .logo {
    height: 100px;
  }

  .present-text {
    font-size: 14px;
  }

  .qr-image {
    height: 60px;
  }

  .nav-item {
    font-size: 14px;
  }

  .dropdown-header {
    font-size: 16px;
    line-height: 16px;
  }
}

/* ==========================================
   MEDIA QUERIES - MOBILE (768px y menor)
   ========================================== */

@media (max-width: 768px) {
  .default-navbar {
    flex-wrap: wrap;
    padding: 12px 16px;
    gap: 8px;
  }

  /* Logo más pequeño */
  .logo {
    height: 70px;
  }

  /* Mostrar hamburguesa */
  .hamburger-btn {
    display: flex;
  }

  /* Menú central se oculta por defecto */
  .center-menu {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    width: 100%;
    flex-direction: column;
    gap: 0;
    justify-content: flex-start;
    background: #572c57;
    padding: 16px 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    z-index: 999;
    max-height: calc(100vh - 70px);
    overflow-y: auto;
  }

  /* Mostrar menú cuando está abierto */
  .center-menu.active {
    display: flex;
  }

  /* Items en mobile (verticales) */
  .nav-item {
    display: block;
    width: 100%;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 14px;
  }

  .auth-menu {
    flex-direction: column;
    width: 100%;
    gap: 0;
  }

  /* Dropdown en mobile */
  .dropdown {
    width: 100%;
  }

  .dropdown-header {
    width: 100%;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    justify-content: space-between;
  }

  .dropdown-container {
    position: static;
    transform: none;
    background: rgba(246, 234, 152, 0.95);
    border-radius: 0;
    box-shadow: none;
    margin-top: 0;
    margin-left: -16px;
    margin-right: -16px;
    margin-bottom: 0;
    width: calc(100% + 32px);
  }

  .dropdown-container a {
    padding: 10px 16px;
    font-size: 14px;
  }

  /* Ocultar QR en mobile (hay espacio limitado) */
  .right-section {
    display: none;
  }

  .hamburger-btn {
    margin-left: auto;
  }
}

/* ==========================================
   MEDIA QUERIES - PEQUEÑOS MÓVILES (480px)
   ========================================== */

@media (max-width: 480px) {
  .default-navbar {
    padding: 10px 12px;
  }

  .logo {
    height: 60px;
  }

  .hamburger-btn span {
    width: 20px;
    height: 2px;
  }

  .nav-item,
  .dropdown-header {
    font-size: 13px;
  }

  .center-menu {
    padding: 12px 12px;
  }

  .dropdown-container {
    margin-left: -12px;
    margin-right: -12px;
    width: calc(100% + 24px);
  }

  .dropdown-container a {
    padding: 8px 12px;
  }
}
</style>
