import { authStore } from '../services/authStore'

/**
 * Validadores de rol simples y funcionales.
 * Retornan booleanos para verificar permisos de usuario.
 */

export const roleHelpers = {
  // Verifica si el usuario está autenticado
  isAuthenticated() {
    return authStore.isLoggedIn && authStore.user
  },

  // Verifica si el usuario es admin
  isAdmin() {
    return this.isAuthenticated() && authStore.user.role === 'admin'
  },

  // Verifica si el usuario es employee
  isEmployee() {
    return this.isAuthenticated() && authStore.user.role === 'employee'
  },

  // Verifica si el usuario es client
  isClient() {
    return this.isAuthenticated() && authStore.user.role === 'client'
  },

  // Verifica si el usuario tiene un rol específico
  hasRole(role) {
    return this.isAuthenticated() && authStore.user.role === role
  },

  // Verifica si el usuario tiene alguno de los roles proporcionados
  hasAnyRole(roles) {
    return this.isAuthenticated() && roles.includes(authStore.user.role)
  },

  // Obtiene el rol del usuario (sin error si no está autenticado)
  getUserRole() {
    return authStore.user?.role || null
  }
}
