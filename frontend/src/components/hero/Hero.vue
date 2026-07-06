<template>
  <section class="hero">
    <!-- Overlay -->
    <div class="overlay"></div>

    <!-- Contenido -->
    <div class="hero-content">
      <h1 class="hero-title">
        Tu esfuerzo <br />
        tiene recompensa
      </h1>

      <p class="hero-subtitle">
        Entrenamientos personalizados, profesores especializados
        y una comunidad que te impulsa a dar siempre un paso más.
      </p>

      <div class="hero-buttons">
        <button class="btn-primary" @click="handleAsociateClick">
          {{ authStore.isLoggedIn ? 'PERFIL' : 'ASOCIATE' }}
        </button>
        <button class="btn-secondary" @click="handleActividadesClick" >ACTIVIDADES</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { authStore } from '../../services/authStore'

const router = useRouter()

// Función para manejar el click del botón ASOCIATE
const handleAsociateClick = () => {
  if (authStore.isLoggedIn) {
    // Si está autenticado, ir a editar perfil
    router.push('/configuracion')
  } else {
    // Si no está autenticado, ir a register
    router.push('/register')
  }
}

// Función para manejar el click del botón ACTIVIDADES
const handleActividadesClick = () => {
  if (!authStore.isLoggedIn) {
    router.push('/actividades')
  } else if (
    authStore.user.role === 'admin' ||
    authStore.user.role === 'employee'
  ) {
    router.push('/dashboard')
  } else {
    router.push('/actividades')
  }
}
</script>

<style scoped>
.hero {
  position: relative;
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  padding-left: 80px;
  padding-top: 100px;
  background-image: url('/hero-background.jpg');
  background-size: cover;
  background-position: center;
  overflow: hidden;
}

/* Overlay violeta */
.overlay {
  position: absolute;
  inset: 0;
  background: rgba(88, 44, 87, 0.65);
  z-index: 1;
}

/* Contenido */
.hero-content {
  position: relative;
  z-index: 2;
  max-width: 600px;
  color: white;
  background-color: transparent;
  padding-right: 20px;
}

/* Título */
.hero-title {
  font-weight: 500;
  line-height: 1;
  margin-bottom: 20px;
}

/* Subtítulo */
.hero-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 30px;
  max-width: 90%;
}

/* Botones */
.hero-buttons {
  display: flex;
  gap: 16px;
  background-color: transparent;
  flex-wrap: wrap;
}

.btn-primary {
  padding-inline: 28px;
}

.btn-secondary {
  padding-inline: 28px;
}

/* ==========================================
   MEDIA QUERIES - TABLET (1024px)
   ========================================== */

@media (max-width: 1024px) {
  .hero {
    padding-left: 40px;
    padding-top: 80px;
  }

  .hero-subtitle {
    font-size: 14px;
  }

  .btn-primary,
  .btn-secondary {
    padding-inline: 20px;
  }
}

/* ==========================================
   MEDIA QUERIES - MOBILE (768px)
   ========================================== */

@media (max-width: 768px) {
  .hero {
    height: 100vh;
    min-height: 500px;
    padding-left: 20px;
    padding-top: 80px;
    align-items: center;
    justify-content: center;
  }

  .hero-content {
    max-width: 100%;
    text-align: center;
    padding-right: 20px;
    padding-left: 0;
  }

  .hero-title {
    line-height: 1.2;
    margin-bottom: 16px;
  }

  .hero-subtitle {
    font-size: 13px;
    margin-bottom: 24px;
    max-width: 100%;
  }

  .hero-buttons {
    justify-content: center;
    gap: 12px;
  }

  .btn-primary,
  .btn-secondary {
    flex: 1;
    max-width: 150px;
  }
}

/* ==========================================
   MEDIA QUERIES - PEQUEÑOS MÓVILES (480px)
   ========================================== */

@media (max-width: 480px) {
  .hero {
    padding-left: 0;
    padding-top: 70px;
    min-height: 400px;
  }

  .hero-content {
    padding: 16px;
    max-width: 100%;
  }

  .hero-title {
    margin-bottom: 12px;
  }

  .hero-subtitle {
    font-size: 12px;
    margin-bottom: 16px;
  }

  .hero-buttons {
    flex-direction: column;
    gap: 10px;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    max-width: none;
  }
}
</style>
