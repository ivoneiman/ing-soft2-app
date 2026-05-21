<template>
  <div class="register-container">
    <h2>Crear cuenta</h2>
    <form @submit.prevent="onSubmit">

      <div class="field">
        <label for="username">Nombre</label>
        <input id="username" v-model="form.username" type="text" placeholder="Juan" />
      </div>

      <div class="field">
        <label for="apellido">Apellido</label>
        <input id="apellido" v-model="form.apellido" type="text" placeholder="Pérez" />
      </div>

      <div class="field">
        <label for="dni">DNI</label>
        <input id="dni" v-model="form.dni" type="text" placeholder="45678912" />
      </div>

      <div class="field">
        <label for="telefono">Teléfono</label>
        <input id="telefono" v-model="form.telefono" type="text" placeholder="221 4676789" />
      </div>

      <div class="field">
        <label for="email">Email</label>
        <input id="email" v-model="form.email" type="email" placeholder="juan@mail.com" />
      </div>

      <div class="field">
        <label for="password">Contraseña</label>
        <input id="password" v-model="form.password" type="password" placeholder="Mínimo 6 caracteres" />
        <small class="hint">Debe tener al menos 6 caracteres</small>
      </div>

      <div v-if="error" class="msg error">{{ error }}</div>
      <div v-if="success" class="msg success">{{ success }}</div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Registrando...' : 'Registrarse' }}
      </button>

    </form>

    <p class="link-text">
      ¿Ya tenés cuenta?
      <RouterLink to="/login">Iniciar sesión</RouterLink>
    </p>
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
  if (password.length < 6)
    return 'La contraseña debe tener al menos 6 caracteres'
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
.register-container {
  max-width: 420px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #eee;
  border-radius: 8px;
}

.field {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

.field label {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.field input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
}

.hint {
  color: #666;
  font-size: 0.78rem;
  margin-top: 0.25rem;
}

.msg {
  margin-bottom: 1rem;
  padding: 0.6rem 0.9rem;
  border-radius: 6px;
  font-size: 0.9rem;
}

.error   { background: #fee2e2; color: #b91c1c; }
.success { background: #dcfce7; color: #15803d; }

button {
  width: 100%;
}

button:disabled { opacity: 0.6; cursor: not-allowed; }

.link-text {
  margin-top: 1rem;
  text-align: center;
  font-size: 0.9rem;
}
</style>
