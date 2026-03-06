import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../services/authStore'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: LoginView },
  { path: '/register', component: RegisterView },
  {
    path: '/dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }  // Esta ruta requiere estar logueado
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Guard de navegación: verifica autenticación antes de cada ruta protegida
router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    // Si no tenemos usuario en memoria, intentamos cargarlo desde la sesión
    if (!authStore.user) {
      await authStore.fetchCurrentUser()
    }
    if (!authStore.isLoggedIn) {
      return { path: '/login' }
    }
  }
})

export default router
