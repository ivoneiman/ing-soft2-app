import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import HomeView from "../views/HomeView.vue";
import { getCurrentUser } from "../services/api";

const routes = [
  { path: "/login", name: "Login", component: LoginView },
  { path: "/register", name: "Register", component: RegisterView },
  // Ruta protegida: requiere autenticación
  { path: "/", name: "Home", component: HomeView, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard: se ejecuta antes de cada cambio de ruta
router.beforeEach(async (to, from, next) => {
  // Si la ruta requiere autenticación...
  if (to.meta.requiresAuth) {
    try {
      // Intentamos obtener el usuario actual (verifica sesión en backend)
      await getCurrentUser();
      next(); // Usuario autenticado, permite el acceso
    } catch (err) {
      // Si no hay sesión, redirige a login
      next("/login");
    }
  } else {
    // Ruta pública, permite el acceso
    next();
  }
});

export default router;
