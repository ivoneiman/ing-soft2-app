import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import HomeView from "../views/HomeView.vue";
// New placeholder views (create empty .vue files if needed)
import ActividadesView from "../views/ActividadesView.vue";
import SobreNosotrosView from "../views/SobreNosotrosView.vue";
import ConfiguracionView from "../views/ConfiguracionView.vue";
import PagosView from "../views/PagosView.vue";
import ReportesView from "../views/ReportesView.vue";

const routes = [
  { path: "/login", name: "Login", component: LoginView },
  { path: "/register", name: "Register", component: RegisterView },
  { path: "/", name: "Home", component: HomeView },
  { path: "/actividades", name: "Actividades", component: ActividadesView },
  { path: "/sobre-nosotros", name: "SobreNosotros", component: SobreNosotrosView },
  { path: "/configuracion", name: "Configuracion", component: ConfiguracionView },
  { path: "/pagos", name: "Pagos", component: PagosView },
  { path: "/reportes", name: "Reportes", component: ReportesView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
