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
const ConfiguracionNotificacionView = () => import("../views/configuracion/NotificationConfigurationView.vue");
const PagosView = () => import("../views/pagos/PagosView.vue");
const ReportesView = () => import("../views/reportes/ReportesView.vue");
const MyQrView = () => import("../views/actividades/MyQrView.vue");
const AttendanceClassesView = () => import("../views/actividades/AttendanceClassesView.vue");
const ScanQrView = () => import("../views/actividades/ScanQrView.vue");
const ReporteUsuariosView = () => import("../views/reportes/ReporteUsuariosView.vue");
const ReportePagosView = () => import("../views/reportes/ReportePagosView.vue");
const MisClasesView = () => import("../views/actividades/MisClasesView.vue");
const CrearUsuarioView = () => import("../views/usuarios/CrearUsuarioView.vue");
// Vistas de Administración de Profesores
const ProfesoresAdminView = () => import("../views/admin/ProfesoresAdminView.vue");
const ListarProfesoresView = () => import("../views/admin/ListarProfesoresView.vue");
const CrearProfesorView = () => import("../views/admin/CrearProfesorView.vue");
const CrearClaseView = () => import("../views/actividades/CrearClaseView.vue");
 
// 🌟 CORRECCIÓN 1: El archivo físico se llama index.vue en tu carpeta dashboard
const DashboardView = () => import("../views/dashboard/DashboardView.vue"); 

const routes = [
  // 🔵 Layout principal (con navbar)
  // 🔵 Layout principal (con navbar)
  {
    path: "/",
    component: MainLayout,
    children: [
      {
        path: "",
        name: "Home",
        component: HomeView,
        meta: { requiresAuth: true }
      },
      {
        path: "actividades",
        name: "Actividades",
        component: ActividadesView,
        meta: { requiresAuth: true }
      },
      {
        path: "sobre-nosotros",
        name: "SobreNosotros",
        component: SobreNosotrosView,
        meta: { requiresAuth: true }
      },
      {
        path: "configuracion",
        name: "Configuracion",
        component: ConfiguracionView,
        meta: { requiresAuth: true }
      },
      {
        path: "configuracion/notificacion",
        name: "ConfiguracionNotificacion",
        component: ConfiguracionNotificacionView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: "pagos",
        name: "Pagos",
        component: PagosView,
        meta: { requiresAuth: true }
      },
      {
        path: "reportes",
        component: ReportesView,
        meta: { requiresAuth: true, requiresAdmin: true },
        children: [
          {
            path: 'usuarios',
            name: 'ReporteUsuarios',
            component: ReporteUsuariosView,
          },
          {
            path: 'pagos',
            name: 'ReportePagos',
            component: ReportePagosView,
          }
        ]
      },
      {
        path: "mi-qr",
        name: "MiQr",
        component: MyQrView,
        meta: { requiresAuth: true, requiresClient: true }
      },
      {
        path: "/admin/profesores",
        name: "AdminProfesores",
        component: ProfesoresAdminView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "/admin/profesores/listar",
        name: "ListarProfesores",
        component: ListarProfesoresView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "/admin/profesores/crear",
        name: "CrearProfesor",
        component: CrearProfesorView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "/admin/profesores/editar/:id",
        name: "EditarProfesor",
        component: () => import("../views/admin/EditarProfesorView.vue"),
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "/admin/clases/crear",
        name: "CrearClase",
        component: CrearClaseView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "/admin/usuarios/crear",
        name: "CrearUsuario",
        component: CrearUsuarioView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "dashboard",
        name: "Dashboard",
        component: DashboardView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true },
      },
      {
        path: "pasar-asistencia",
        name: "PasarAsistencia",
        component: AttendanceClassesView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true }
      },
      {
        path: "pasar-asistencia/:classId",
        name: "ScanQr",
        component: ScanQrView,
        meta: { requiresAuth: true, requiresAdminOrEmployee: true }
      },
      {
        path: "mis-clases",
        name: "MisClases",
        component: MisClasesView,
        meta: { requiresAuth: true, requiresClient: true }
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
 */
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin);
  const requiresEmployee = to.matched.some(record => record.meta.requiresEmployee);
  const requiresAdminOrEmployee = to.matched.some(record => record.meta.requiresAdminOrEmployee);
  const requiresClient = to.matched.some(record => record.meta.requiresClient);

  if (requiresAuth && !roleHelpers.isAuthenticated()) {
    await authStore.fetchCurrentUser();
  }

  if (requiresAuth && !roleHelpers.isAuthenticated()) {
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }

  if (requiresAdminOrEmployee && !roleHelpers.hasAnyRole(['admin', 'employee'])) {
    return next('/');
  }

  if (requiresAdmin && !roleHelpers.isAdmin()) {
    return next('/');
  }

  if (requiresEmployee && !roleHelpers.isEmployee()) {
    return next('/');
  }

  if (requiresClient && !roleHelpers.isClient()) {
    return next('/');
  }

  next();
});

export default router;
