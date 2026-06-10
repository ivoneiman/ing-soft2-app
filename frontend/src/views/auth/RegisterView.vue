<template>
  <div class="login-page">
    <div class="login-card">
      
      <div class="brand-header">
        <img src="/logo-con-aura.png" alt="SiempreGym Logo" class="brand-logo" />
      </div>

      <h2>Crear cuenta</h2>
      <p class="subtitle">Completá tus datos para registrarte</p>

      <form @submit.prevent="onSubmit" class="login-form">

        <div class="form-row">
          <div class="input-group">
            <label for="username">Nombre</label>
            <input id="username" v-model="form.username" type="text" placeholder="Juan" required />
          </div>
          <div class="input-group">
            <label for="apellido">Apellido</label>
            <input id="apellido" v-model="form.apellido" type="text" placeholder="Pérez" required />
          </div>
        </div>

        <div class="form-row">
          <div class="input-group">
            <label for="dni">DNI</label>
            <input id="dni" v-model="form.dni" type="text" placeholder="45678912" required />
          </div>
          <div class="input-group">
            <label for="telefono">Teléfono</label>
            <input id="telefono" v-model="form.telefono" type="text" placeholder="221 4676789" required />
          </div>
        </div>

        <div class="input-group">
          <label for="email">Email</label>
          <input id="email" v-model="form.email" type="email" placeholder="juan@mail.com" required />
        </div>

        <div class="input-group">
          <label for="password">Contraseña</label>
          <input id="password" v-model="form.password" type="password" placeholder="Mínimo 6 caracteres, 1 mayúscula y 1 símbolo" required />
          <small class="hint">Debe tener al menos 6 caracteres, 1 mayúscula y 1 símbolo especial (?, !, ", #, etc.)</small>
        </div>

        <div v-if="error" class="msg error">{{ error }}</div>
        <div v-if="success" class="msg success">{{ success }}</div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? 'Registrando...' : 'Registrarse' }}
        </button>

      </form>

      <p class="link-text">
        ¿Ya tenés cuenta?
        <RouterLink to="/login">Iniciar sesión</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { RouterLink } from 'vue-router'
import { register } from '../../services/api'

const form = reactive({
  username: '',
  apellido: '',
  dni: '',
  telefono: '',
  email: '',
  password: ''
})

const error   = ref('')
const success = ref('')
const loading = ref(false)

function validarPassword(password) {
  if (password.length < 6) {
    return 'La contraseña debe tener al menos 6 caracteres'
  }
  if (!/[A-Z]/.test(password)) {
    return 'La contraseña debe incluir al menos una letra mayúscula'
  }
  if (!/[^a-zA-Z0-9]/.test(password)) {
    return 'La contraseña debe incluir al menos un símbolo especial (?, !, ", #, etc.)'
  }
  return null
}

async function onSubmit() {
  error.value   = ''
  success.value = ''

  const { username, apellido, dni, telefono, email, password } = form

  if (!username.trim() || !apellido.trim() || !dni.trim() ||
      !telefono.trim() || !email.trim() || !password) {
    error.value = 'Debe completar todos los campos'
    return
  }

  const errorPass = validarPassword(password)
  if (errorPass) {
    error.value = errorPass
    return
  }

  loading.value = true
  try {
    await register({ username, apellido, email, dni, telefono, password })
    success.value = 'Usuario registrado correctamente. Ya podés iniciar sesión.'
    Object.keys(form).forEach(k => form[k] = '')
  } catch (err) {
    if (err.response?.data?.error) {
      error.value = err.response.data.error
    } else if (!err.response) {
      error.value = 'No se pudo conectar con el servidor'
    } else {
      error.value = 'Error al registrar usuario'
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
  padding: 4.5rem 2rem 1.5rem; /* Padding reducido para evitar scroll */
  width: 100%;
  max-width: 520px; /* Más ancho para acomodar las dos columnas */
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
  margin-bottom: 1.25rem;
  font-size: 1rem;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.input-group label {
  font-size: 0.95rem;
  text-transform: uppercase;
  color: #572c57;
  letter-spacing: 0.5px;
}

.input-group input {
  padding: 0.7rem 0.85rem;
  border: 1.5px solid #9f5f91;
  border-radius: 8px;
  font-size: 1rem;
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

.hint {
  color: #8a6a8a;
  font-size: 0.8rem;
  margin-top: 0.25rem;
  font-family: 'Bodoni Moda', serif;
}

.btn-submit {
  background: #572c57;
  color: #f6ea98;
  border: none;
  padding: 0.8rem;
  border-radius: 8px;
  font-size: 1.05rem;
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

.success {
  background: rgba(159, 95, 145, 0.15);
  color: #572c57;
  border: 1px solid #9f5f91;
  font-weight: bold;
}

.link-text {
  text-align: center;
  margin-top: 1.25rem;
  font-size: 1rem;
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

@media (max-width: 520px) {
  .login-page {
    padding: 1rem;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
  .login-card {
    padding: 4.5rem 1.5rem 2rem;
    margin-top: 60px;
  }
}
</style>
