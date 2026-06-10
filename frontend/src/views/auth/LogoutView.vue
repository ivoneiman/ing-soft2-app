<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand-header">
        <img src="/logo-con-aura.png" alt="SiempreGym Logo" class="brand-logo" />
      </div>

      <!-- Confirmación antes de cerrar sesión -->
      <div v-if="showConfirm" class="confirm-box">
        <h2>Cerrar sesión</h2>
        <p class="subtitle">¿Estás seguro que querés salir de tu cuenta?</p>
        <div class="buttons">
          <button class="btn-submit" @click="confirmLogout" :disabled="loading">Sí, cerrar sesión</button>
          <button class="btn-secondary" @click="cancelLogout" :disabled="loading">No, volver</button>
        </div>
      </div>

      <!-- Mensaje mientras se procesa el logout -->
      <div v-else class="processing">
        <h2>Cerrando sesión...</h2>
        <p class="subtitle">Por favor esperá un momento.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { logout } from '../../services/api'
import { useRouter } from 'vue-router'

const router = useRouter()
const showConfirm = ref(true) // muestra la ventana de confirmación
const loading = ref(false)

/**
 * Ejecuta el logout y redirige al login.
 */
async function performLogout() {
  loading.value = true
  try {
    await logout()
  } catch (e) {
    // Ignorar errores de logout, seguimos redirigiendo
  } finally {
    router.push('/login')
  }
}

function confirmLogout() {
  showConfirm.value = false
  performLogout()
}

function cancelLogout() {
  // Volver a la página anterior o a home
  router.back()
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Anta&family=Anton&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&display=swap');

.login-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(rgba(87, 44, 87, 0.7), rgba(87, 44, 87, 0.8)), url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1470&auto=format&fit=crop') center/cover no-repeat fixed;
  padding: 2rem 1rem;
  font-family: 'Anta', sans-serif;
}

.login-card {
  background: rgba(245, 245, 245, 0.95); /* #f5f5f5 con ligera transparencia */
  border-radius: 20px;
  padding: 5rem 2rem 2.5rem; /* Aumentamos el padding superior para dar espacio al logo */
  width: 100%;
  max-width: 380px; /* Cuadrado más chico */
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  position: relative;
  margin-top: 70px; /* Margen para que el logo no choque con el techo de la pantalla */
}

.brand-header {
  position: absolute;
  top: -70px; /* Lo sube justo a la mitad de su propia altura */
  left: 50%;
  transform: translateX(-50%); /* Lo centra perfectamente */
  width: 140px;
  height: 140px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
  padding: 15px;
  border: 4px solid #ffffff; /* Borde blanco para resaltar el círculo */
}

.brand-logo {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain; /* Asegura que el logo no se deforme dentro del círculo */
}

.login-card h2 {
  margin: 0 0 0.5rem 0;
  color: #572c57;
  font-size: 1.8rem;
  text-align: center;
}

.subtitle {
  color: #9f5f91;
  margin-bottom: 2rem;
  font-size: 1.05rem;
  text-align: center;
}

.confirm-box {
  text-align: center;
}

.buttons {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.btn-submit {
  background: #572c57;
  color: #f6ea98;
  border: none;
  padding: 0.9rem;
  border-radius: 8px;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, background 0.3s;
  font-family: 'Anta', sans-serif !important;
}

.btn-submit:hover:not(:disabled) {
  background: #9f5f91;
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(87, 44, 87, 0.3);
}

.btn-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #e8dce8;
  color: #572c57;
  border: none;
  padding: 0.9rem;
  border-radius: 8px;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Anta', sans-serif !important;
}

.btn-secondary:hover:not(:disabled) {
  background: #d0c0d0;
  transform: translateY(-2px);
}

.btn-secondary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.processing {
  text-align: center;
  padding: 2rem 0;
}

@media (max-width: 480px) {
  .login-page {
    padding: 1rem;
  }
  .login-card {
    padding: 4.5rem 1.5rem 2rem;
    margin-top: 60px;
  }
}
</style>