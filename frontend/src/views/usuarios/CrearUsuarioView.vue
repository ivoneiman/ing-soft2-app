<template>
  <div class="crear-usuario-container">
    <h2>Crear nuevo usuario</h2>
    <p class="subtitle">Completá los datos del nuevo cliente</p>

    <form @submit.prevent="onSubmit">

      <div class="row">
        <div class="field">
          <label for="username">Nombre</label>
          <input id="username" v-model="form.username" type="text" placeholder="Juan" />
        </div>
        <div class="field">
          <label for="apellido">Apellido</label>
          <input id="apellido" v-model="form.apellido" type="text" placeholder="Pérez" />
        </div>
      </div>

      <div class="row">
        <div class="field">
          <label for="dni">DNI</label>
          <input id="dni" v-model="form.dni" type="text" placeholder="45678912" />
        </div>
        <div class="field">
          <label for="telefono">Teléfono</label>
          <input id="telefono" v-model="form.telefono" type="text" placeholder="221 4561234" />
        </div>
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

      <div class="actions">
        <button type="submit" :disabled="loading">
          {{ loading ? 'Creando...' : 'Crear usuario' }}
        </button>
        <button type="button" class="btn-secondary" @click="limpiarFormulario">
          Limpiar
        </button>
      </div>

    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { crearUsuario } from '../../services/api'

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

function limpiarFormulario() {
  Object.keys(form).forEach(k => form[k] = '')
  error.value   = ''
  success.value = ''
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
    await crearUsuario({ username, apellido, email, dni, telefono, password })
    success.value = 'Usuario creado exitosamente'
    limpiarFormulario()
    success.value = 'Usuario creado exitosamente'
  } catch (err) {
    if (err.response?.data?.error) {
      error.value = err.response.data.error
    } else if (!err.response) {
      error.value = 'No se pudo conectar con el servidor'
    } else {
      error.value = 'Error al crear el usuario'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.crear-usuario-container {
  max-width: 560px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #eee;
  border-radius: 10px;
  background: #fff;
}

h2 { margin-bottom: 0.25rem; color: #572c57; }

.subtitle { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

.field label { font-weight: 600; margin-bottom: 0.25rem; font-size: 0.9rem; }

.field input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
}

.field input:focus { outline: none; border-color: #9f5f91; }

.hint { color: #888; font-size: 0.75rem; margin-top: 0.25rem; }

.msg { margin-bottom: 1rem; padding: 0.6rem 0.9rem; border-radius: 6px; font-size: 0.9rem; }
.error   { background: #fee2e2; color: #b91c1c; }
.success { background: #dcfce7; color: #15803d; }

.actions { display: flex; gap: 0.75rem; }

button {
  flex: 1;
  padding: 0.65rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
}

button[type="submit"] { background: #572c57; color: white; }
button[type="submit"]:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-secondary { background: #f3f4f6; color: #374151; }
.btn-secondary:hover { background: #e5e7eb; }
</style>