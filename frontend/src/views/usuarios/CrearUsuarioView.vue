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
        <label for="role">Tipo de Usuario</label>
        <select id="role" v-model="form.role">
          <option value="client">Cliente</option>
          <option v-if="isAdmin" value="employee">Empleado</option>
          <option v-if="isAdmin" value="admin">Administrador</option>
        </select>
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
import { ref, reactive, onMounted } from 'vue'
import { crearUsuario } from '../../services/api'
import { roleHelpers } from '../../utils/roleHelpers'

const form = reactive({
  username: '',
  apellido: '',
  dni: '',
  telefono: '',
  email: '',
  password: '',
  role: 'client'
})

const error   = ref('')
const success = ref('')
const loading = ref(false)

const isAdmin = ref(false)

onMounted(() => {
  isAdmin.value = roleHelpers.isAdmin()
})

function validarPassword(password) {
  if (password.length < 6)
    return 'La contraseña debe tener al menos 6 caracteres'
  return null
}

function limpiarFormulario() {
  Object.keys(form).forEach(k => {
    if (k === 'role') form[k] = 'client'
    else form[k] = ''
  })
  error.value   = ''
  success.value = ''
}

async function onSubmit() {
  error.value   = ''
  success.value = ''

  const { username, apellido, dni, telefono, email, password, role } = form

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
    await crearUsuario({ username, apellido, email, dni, telefono, password, role })
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
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Anta&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;1,6..96,400&display=swap');

.crear-usuario-container {
  min-height: 100vh;
  background-color: #572c57;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

h2 {
  color: #f6ea98;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
}

.subtitle {
  color: #e2c4e0;
  margin-bottom: 1.5rem;
  font-family: 'Bodoni Moda', serif;
}

form {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 12px;
  padding: 2rem 2rem 2.5rem 2rem;
  width: 100%;
  max-width: 560px;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  margin-bottom: 1.25rem;
}

.field label {
  font-family: 'Anta', sans-serif;
  font-size: 0.85rem;
  color: #f6ea98;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.field input,
.field select {
  padding: 0.6rem 0.75rem;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  font-size: 1rem;
  background: white;
  color: #333;
  font-family: 'Anton', sans-serif;
}

.field input::placeholder { color: #bbb; }
.field input:focus,
.field select:focus {
  outline: none;
  border-color: #e26972;
}

.hint { color: rgba(255,255,255,0.5); font-size: 0.72rem; margin-top: 0.25rem; font-family: 'Bodoni Moda', serif; }

.msg { margin-bottom: 1rem; padding: 0.6rem 0.9rem; border-radius: 6px; font-size: 0.9rem; }
.error   { background: rgba(226,105,114,0.25); color: #f6a5aa; border: 1px solid #e26972; }
.success { background: rgba(74,222,128,0.15); color: #86efac; border: 1px solid #4ade80; }

.actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }

button {
  flex: 1;
  text-transform: uppercase;
}

button[type="submit"]:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
