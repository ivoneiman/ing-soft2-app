<!--
  Vista principal (Home) después de iniciar sesión.
  Muestra un mensaje de bienvenida con el nombre de usuario y email obtenidos
  mediante una llamada a la API (`getCurrentUser`). Mientras la petición está
  en curso muestra "Cargando usuario..."; si no hay sesión redirige al login.
-->
<template>
  <div>
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
// `useRouter` permite navegar programáticamente entre rutas

// Estado reactivo del componente
const user = ref(null)      // contendrá el objeto usuario cuando se cargue
const loading = ref(true)   // indica si la petición al backend está en curso

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
