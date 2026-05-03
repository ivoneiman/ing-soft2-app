import { createRouter, createWebHistory } from "vue-router";

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
      },
      {
        path: "pagos",
        name: "Pagos",
        component: PagosView,
      },
      {
        path: "reportes",
        name: "Reportes",
        component: ReportesView,
      },
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

export default router;
