<!--
  Vista principal (Home) después de iniciar sesión.
  Muestra un mensaje de bienvenida con el nombre de usuario y email obtenidos
  mediante una llamada a la API (`getCurrentUser`). Mientras la petición está
  en curso muestra "Cargando usuario..."; si no hay sesión redirige al login.
-->
<template>
  <div class="home-container">
    <div v-if="user" class="welcome-box">
      <h2>¡Hola, {{ formatName(user.apellido, user.username) }}!</h2>
      <p>Bienvenido de nuevo a SiempreGym</p>
    </div>

    <div v-if="roleHelpers.hasAnyRole(['admin', 'employee'])" class="role-badge">
      Estás navegando como: <strong>{{ roleHelpers.isAdmin() ? 'Administrador' : 'Empleado' }}</strong>
    </div>

    <Hero />
  </div>
</template>

<script setup>
// Importamos `ref` para crear variables reactivas y `onMounted` para ejecutar código
// cuando el componente se inserta en el DOM (similar a componentDidMount en React)
import { ref, onMounted } from 'vue'
import Hero from '../../components/hero/Hero.vue'
// `getCurrentUser` obtiene los datos del usuario autenticado; `logout` cierra la sesión
import { getCurrentUser } from '../../services/api'
import { roleHelpers } from '../../utils/roleHelpers'
// `useRouter` permite navegar programáticamente entre rutas

// Estado reactivo del componente
const user = ref(null)      // contendrá el objeto usuario cuando se cargue
const loading = ref(true)   // indica si la petición al backend está en curso

function formatName(apellido, nombre) {
  const formatWord = (w) => (w ? w.toString().toLowerCase().replace(/\b\w/g, l => l.toUpperCase()) : '');
  return `${formatWord(nombre)} ${formatWord(apellido)}`.trim();
}

// Cuando el componente se monta, solicitamos al backend los datos del usuario actual
onMounted(async () => {
  try {
    const response = await getCurrentUser()
    user.value = response.data.user
  } catch (err) {
    // Si la petición falla (p.ej. sesión inexistente), simplemente no hacemos nada.
    // Se podría mostrar un mensaje o manejar el error de otra forma.
    user.value = null
  } finally {
    loading.value = false // finalizamos el indicador de carga
  }
})

// Cierra la sesión del usuario y lo redirige al login
// Logout functionality moved to a dedicated view (LogoutView.vue)
</script>

<style scoped>
.home-container {
  position: relative;
}

.role-badge {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background-color: #f6ea98;
  color: #572c57;
  padding: 12px 24px;
  border-radius: 50px;
  font-size: 0.95rem;
  font-weight: 500;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.role-badge strong {
  font-weight: 800;
  text-transform: uppercase;
}

.welcome-box {
  text-align: center;
  margin-top: 2rem;
  color: #572c57;
}
.welcome-box h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
.welcome-box p {
  color: #8a6a8a;
  font-size: 1.1rem;
}

img {
  max-width: 300px;
  height: auto;
  width: 100%;
  object-fit: cover;
}

/* ==========================================
   MEDIA QUERIES - TABLET (1024px)
   ========================================== */

@media (max-width: 1024px) {
  img {
    max-width: 250px;
  }
}

/* ==========================================
   MEDIA QUERIES - MOBILE (768px)
   ========================================== */

@media (max-width: 768px) {
  img {
    max-width: 200px;
  }
}

/* ==========================================
   MEDIA QUERIES - PEQUEÑOS MÓVILES (480px)
   ========================================== */

@media (max-width: 480px) {
  img {
    max-width: 150px;
  }
}
</style>