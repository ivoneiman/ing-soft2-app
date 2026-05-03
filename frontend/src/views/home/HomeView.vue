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
import { useRouter } from 'vue-router'

// Estado reactivo del componente
const user = ref(null)      // contendrá el objeto usuario cuando se cargue
const loading = ref(true)   // indica si la petición al backend está en curso
const router = useRouter()  // router for navigation

// Cuando el componente se monta, solicitamos al backend los datos del usuario actual
onMounted(async () => {
  try {
    const response = await getCurrentUser()
    user.value = response.data.user
  } catch (err) {
    // Si la petición falla (p.ej. sesión inexistente), redirigimos al login
    router.push('/login')
  } finally {
    loading.value = false // finalizamos el indicador de carga
  }
})

// Cierra la sesión del usuario y lo redirige al login
// Logout functionality moved to a dedicated view (LogoutView.vue)
</script>

<style scoped>

img{
  height: 300px;
  width: 300px;
}
</style>
