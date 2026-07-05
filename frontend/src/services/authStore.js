import { reactive } from 'vue'
import { login, register, logout, getCurrentUser, adminLoginRequest, adminLoginVerify } from './api'

// Estado global de autenticación (composable simple sin Pinia)
// Si el proyecto crece, conviene usar Pinia como store
export const authStore = reactive({
  user: null,
  loading: false,
  error: null,
  needs2FA: false, // Nuevo estado para manejar el flujo de admin
  isLoggedIn: false,

  async fetchCurrentUser() {
    try {
      const res = await getCurrentUser()
      this.user = res.data.user
      this.isLoggedIn = true
    } catch {
      this.user = null
      this.isLoggedIn = false
    }
  },

  async login(email, password) {
    this.loading = true
    this.error = null
    try {
      // Esta llamada ahora va a un endpoint unificado en el backend
      const res = await login({ email, password })

      // Si el backend indica que se necesita 2FA (porque es un admin)
      if (res.data.needs2FA) {
        this.needs2FA = true
        // No se loguea al usuario todavía, solo se avanza al siguiente paso
        return true // La primera fase fue exitosa
      } else {
        // Si es un cliente o empleado, el login es directo
        this.user = res.data.user
        this.isLoggedIn = true
        this.needs2FA = false
        return true
      }
    } catch (err) {
      this.error = err.response?.data?.error || 'Error al iniciar sesión'
      return false
    } finally {
      this.loading = false
    }
  },

  async adminLoginVerify(email, code) {
    this.loading = true
    this.error = null
    try {
      const res = await adminLoginVerify({ email, code })
      this.user = res.data.user
      this.isLoggedIn = true
      this.needs2FA = false // Se completa el flujo 2FA
      return true
    } catch (err) {
      this.error = err.response?.data?.error || 'Error al verificar el código'
      return false
    } finally {
      this.loading = false
    }
  },

  async register({ username, apellido, email, dni, telefono, password }) {
    this.loading = true
    this.error = null
    try {
      await register({ username, apellido, email, dni, telefono, password })
      // Después de registrar, hacer login automático
      return await this.login(email, password)
    } catch (err) {
      this.error = err.response?.data?.error || 'Error al registrarse'
      return false
    } finally {
      this.loading = false
    }
  },

  async logout() {
    try {
      await logout()
    } catch (err) {
      console.error('Error al cerrar sesión:', err)
    } finally {
      this.user = null
      this.isLoggedIn = false
      this.needs2FA = false
    }
  }
})
