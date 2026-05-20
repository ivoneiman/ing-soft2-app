import { createRouter, createWebHistory } from "vue-router";
import { authStore } from "../services/authStore";
import { roleHelpers } from "../utils/roleHelpers";

// layouts
import MainLayout from "../layouts/MainLayout.vue";
import AuthLayout from "../layouts/AuthLayout.vue";

// views
import HomeView from "../views/home/HomeView.vue";
import LoginView from "../views/auth/LoginView.vue";
import RegisterView from "../views/auth/RegisterView.vue";
import LogoutView from "../views/auth/LogoutView.vue";

// lazy (mejor práctica)
const ActividadesView = () => import("../views/actividades/ActividadesView.vue");
const SobreNosotrosView = () => import("../views/sobre-nosotros/SobreNosotrosView.vue");
const ConfiguracionView = () => import("../views/configuracion/ConfiguracionView.vue");
const PagosView = () => import("../views/pagos/PagosView.vue");
const ReportesView = () => import("../views/reportes/ReportesView.vue");
const MyQrView = () => import("../views/actividades/MyQrView.vue");
const ScanQrView = () => import("../views/actividades/ScanQrView.vue");
const CrearClaseView = () => import("../views/actividades/CrearClaseView.vue");
const CrearUsuarioView = () => import("../views/usuarios/CrearUsuarioView.vue"); 
const AdminDiscountsView = () => import("../views/pagos/AdminDiscountsView.vue");


const routes = [
  // 🔵 Layout principal (con navbar)
  {
    path: "/",
    component: MainLayout,
    children: [
      {
        path: "",
        name: "Home",
        component: HomeView,
      },
      {
        path: "actividades",
        name: "Actividades",
        component: ActividadesView,
      },
      {
        path: "sobre-nosotros",
        name: "SobreNosotros",
        component: SobreNosotrosView,
      },
      {
        path: "configuracion",
        name: "Configuracion",
        component: ConfiguracionView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: "pagos",
        name: "Pagos",
        component: PagosView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: "reportes",
        name: "Reportes",
        component: ReportesView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: "mi-qr",
        name: "MiQr",
        component: MyQrView,
        meta: { requiresAuth: true, requiresClient: true }
      },
      {
        path: "pasar-asistencia",
        name: "PasarAsistencia",
        component: ScanQrView,
        meta: { requiresAuth: true, requiresEmployee: true }
      },
      {
        path: "crear-clase",
        name: "CrearClase",
        component: CrearClaseView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "crear-usuario",
        name: "CrearUsuario",
        component: CrearUsuarioView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "admin/descuentos",
        name: "AdminDiscounts",
        component: AdminDiscountsView,
        meta: { requiresAuth: true, requiresAdmin: true },
      }
    ],
  },

  // 🟣 Auth (sin navbar)
  {
    path: "/",
    component: AuthLayout,
    children: [
      {
        path: "login",
        name: "Login",
        component: LoginView,
      },
      {
        path: "register",
        name: "Register",
        component: RegisterView,
      },
      {
        path: "logout",
        name: "Logout",
        component: LogoutView,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

/**
 * Guard de navegación global
 * Valida:
 * - requiresAuth: usuario debe estar autenticado
 * - requiresAdmin: usuario debe ser admin
 * - requiresEmployee: usuario debe ser employee
 * - requiresClient: usuario debe ser client
 */
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
  const requiresEmployee = to.matched.some(record => record.meta.requiresEmployee);
  const requiresAdminOrEmployee = to.matched.some(record => record.meta.requiresAdminOrEmployee); // agregué eso porque algunas cosas las tienen que poder usar los empleados y los admins
  const requiresClient = to.matched.some(record => record.meta.requiresClient);

  // Si no está autenticado y la ruta lo requiere, redirigir a login
  if (requiresAuth && !roleHelpers.isAuthenticated()) {
    return next('/login');
  }

  // Validar rol admin o employee
  if (requiresAdminOrEmployee && !roleHelpers.hasAnyRole(['admin', 'employee'])) {
    return next('/');
  }

  // Validar rol admin
  if (requiresAdmin && !roleHelpers.isAdmin()) {
    return next('/');
  }

  // Validar rol employee
  if (requiresEmployee && !roleHelpers.isEmployee()) {
    return next('/');
  }

  // Validar rol client
  if (requiresClient && !roleHelpers.isClient()) {
    return next('/');
  }

  next();
});

export default router;
