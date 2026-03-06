import { reactive } from 'vue'
import { authService } from './api'

// Estado global de autenticación (composable simple sin Pinia)
// Si el proyecto crece, conviene usar Pinia como store
export const authStore = reactive({
  user: null,
  loading: false,
  error: null,

  async fetchCurrentUser() {
    try {
      const res = await authService.me()
      this.user = res.data.user
    } catch {
      this.user = null
    }
  },

  async login(email, password) {
    this.loading = true
    this.error = null
    try {
      const res = await authService.login(email, password)
      this.user = res.data.user
      return true
    } catch (err) {
      this.error = err.response?.data?.error || 'Error al iniciar sesión'
      return false
    } finally {
      this.loading = false
    }
  },

  async register(username, email, password) {
    this.loading = true
    this.error = null
    try {
      const res = await authService.register(username, email, password)
      this.user = res.data.user
      return true
    } catch (err) {
      this.error = err.response?.data?.error || 'Error al registrarse'
      return false
    } finally {
      this.loading = false
    }
  },

  async logout() {
    await authService.logout()
    this.user = null
  },

  get isLoggedIn() {
    return !!this.user
  }
})
