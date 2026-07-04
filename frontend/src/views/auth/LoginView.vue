<!--
  Vista de inicio de sesión.
  Presenta un formulario que solicita email y contraseña, llama a la API de login
  y, si la autenticación es exitosa, redirige al usuario a la página principal.
  También muestra un enlace a la vista de registro.
-->
<template>
  <div class="login-page">
    <div class="login-card">
      
      <div class="brand-header">
        <img src="/logo-con-aura.png" alt="SiempreGym Logo" class="brand-logo" />
      </div>

        <h2>Bienvenido de nuevo</h2>
        <p class="subtitle">Iniciá sesión para continuar</p>

        <form @submit.prevent="onSubmit" class="login-form">
          <div class="input-group">
            <label for="email">Email</label>
            <input id="email" v-model="email" type="email" placeholder="tu@email.com" :disabled="adminLoginStep" required />
          </div>

          <div class="input-group" v-if="!adminLoginStep">
            <label for="password">Contraseña</label>
            <input id="password" v-model="password" type="password" placeholder="••••••••" required />
          </div>

          <div class="input-group" v-if="adminLoginStep">
            <label for="code">Código de verificación</label>
            <input id="code" v-model="code" type="text" maxlength="6" placeholder="123456" required />
          </div>

          <button type="submit" class="btn-submit" :disabled="loading">
            {{ adminLoginStep ? 'Verificar código' : 'Ingresar' }}
          </button>
          <div v-if="error" class="msg error">{{ error }}</div>
          <div v-if="info" class="msg info">{{ info }}</div>
        </form>
        
        <!-- Enlace a la vista de registro.-->
        <p class="link-text" v-if="!adminLoginStep">
          ¿No tenés cuenta?
          <RouterLink to="/register">Crear cuenta</RouterLink>
        </p>
    </div>
  </div>
</template>

<script setup>

import { ref } from 'vue'
import { authStore } from '../../services/authStore'
import { RouterLink, useRoute, useRouter } from 'vue-router'
// Variables reactivas para manejar el estado del formulario y el estado UI.
const route = useRoute()
const router = useRouter()
const mode = ref('password') // Se mantiene por si se quiere reutilizar, pero el flujo es único.
const email = ref('') //email ingresado por el usuario
const password = ref('')// contraseña ingresada por el usuario
const code = ref('')
const error = ref('')// mensaje de error a mostrar al usuario
const info = ref('')
const loading = ref(false)//indica si peticion está en curso
const adminLoginStep = ref(false) // true si el login es de admin y se espera el código

function redirectAfterLogin() {
  router.push(route.query.redirect || '/')
}

async function onSubmit() {
  // Reiniciamos el mensaje de error y marcamos carga
  error.value = ''
  info.value = ''
  loading.value = true

  try {
    // Si estamos en el paso de verificación de código para admin
    if (adminLoginStep.value) {
      if (!code.value.trim()) {
        error.value = 'Debes ingresar el código de verificación.'
        return
      }
      const ok = await authStore.adminLoginVerify(email.value, code.value.trim())
      if (ok) {
        redirectAfterLogin()
      } else {
        error.value = authStore.error || 'El código es incorrecto o ha expirado.'
      }
    } else {
      // Paso inicial: enviar email y contraseña
      if (!email.value.trim() || !password.value.trim()) {
        error.value = 'Debes completar tu email y contraseña.'
        return
      }

      // `authStore.login` ahora maneja la lógica de roles.
      // Si el backend responde con `needs2FA: true`, el usuario es un admin
      // y se debe proceder al segundo paso.
      const ok = await authStore.login(email.value, password.value)

      if (ok) {
        // Si el login fue exitoso y NO requiere 2FA (es cliente o empleado),
        // se redirige directamente.
        if (!authStore.needs2FA) {
          redirectAfterLogin()
        } else {
          // Si es admin, el backend ya envió el código.
          // Mostramos el campo para el código y un mensaje informativo.
          info.value = 'Le enviamos un código a su email para completar su autenticación.'
          adminLoginStep.value = true // Esto muestra el campo del código
        }
      } else {
        error.value = authStore.error
      }
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Anta&family=Anton&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&display=swap');

.login-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  /* Imagen grande de fondo con un pequeño oscurecimiento/overlay morado */
  background: linear-gradient(rgba(87, 44, 87, 0.7), rgba(87, 44, 87, 0.8)), url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1470&auto=format&fit=crop') center/cover no-repeat fixed;
  padding: 2rem 1rem;
  font-family: 'Anta', sans-serif;
}

.login-card {
  background: rgba(245, 245, 245, 0.95); /* #f5f5f5 con ligera transparencia */
  border-radius: 20px;
  padding: 5rem 2rem 2.5rem; /* Aumentamos el padding superior para dar espacio al logo */
  width: 100%;
  max-width: 380px; /* Cuadrado de login más chico */
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

.mode-buttons {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  background: #e8dce8; /* Tono suave derivado del morado para la botonera */
  padding: 0.35rem;
  border-radius: 10px;
}

.mode-button {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  color: #572c57;
  cursor: pointer;
  border-radius: 8px;
  font-size: 0.9rem;
  text-transform: uppercase;
  transition: all 0.3s ease;
}

.mode-button.active {
  background: #f6ea98;
  color: #572c57;
  box-shadow: 0 2px 8px rgba(87, 44, 87, 0.15);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.input-group label {
  font-size: 0.95rem;
  text-transform: uppercase;
  color: #572c57;
  letter-spacing: 0.5px;
}

.input-group input {
  padding: 0.85rem 1rem;
  border: 1.5px solid #9f5f91;
  border-radius: 8px;
  font-size: 1.05rem;
  transition: all 0.3s ease;
  font-family: system-ui, -apple-system, sans-serif !important;
  background: #ffffff;
  color: #572c57;
}

.input-group input::placeholder {
  font-family: system-ui, -apple-system, sans-serif !important;
  color: #bfaabf;
}

.input-group input:focus {
  outline: none;
  border-color: #9f5f91;
  box-shadow: 0 0 0 4px rgba(159, 95, 145, 0.15);
}

.input-group input:disabled {
  background: #e8dce8;
  cursor: not-allowed;
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
  margin-top: 0.5rem;
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

.msg {
  padding: 0.8rem;
  border-radius: 8px;
  font-size: 0.9rem;
  text-align: center;
}

.error {
  background: #f6ea98;
  color: #572c57;
  border: 1px solid #dcd181;
  font-weight: bold;
}

.info {
  background: rgba(159, 95, 145, 0.15);
  color: #572c57;
  border: 1px solid #9f5f91;
}

.link-text {
  text-align: center;
  margin-top: 2rem;
  font-size: 1.05rem;
  color: #572c57;
}

.link-text a {
  color: #9f5f91;
  text-decoration: none;
  margin-left: 0.3rem;
}

.link-text a:hover {
  text-decoration: underline;
  color: #572c57;
}

@media (max-width: 900px) {
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