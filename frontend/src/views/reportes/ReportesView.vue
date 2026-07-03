<template>
  <div class="reportes-view">
    <header class="page-header">
      <h1>Reportes y Administración</h1>
      <p>Seleccioná el módulo que deseas consultar.</p>
    </header>

    <!-- Aquí se renderizará el componente hijo (ReporteUsuariosView o ReportePagosView) -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>

    <!-- Las tarjetas de navegación solo se mostrarán si estamos en la ruta base /reportes -->
    <div v-if="$route.path === '/reportes'" class="reports-grid">
      <router-link to="/reportes/usuarios" class="report-card">
        <h3>Directorio de Usuarios</h3>
        <p>Visualizar perfiles, contactar e inspeccionar inscripciones.</p>
      </router-link>

      <router-link to="/reportes/pagos" class="report-card">
        <h3>Historial de Pagos</h3>
        <p>Visualizar todos los pagos realizados, señas y transacciones pendientes.</p>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { RouterLink, RouterView, useRoute } from "vue-router";

// useRoute es necesario para que $route sea reactivo en el template
const route = useRoute();
</script>

<style scoped>
.reportes-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 140px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  color: #fff;
  margin: 0 0 0.5rem 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.page-header p {
  color: #e0c0e0;
  font-size: 1.05rem;
  margin: 0;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.report-card {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 12px;
  padding: 1.5rem;
  text-decoration: none;
  color: #4a3a4a;
  transition: all 0.3s ease;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  display: block;
}

.report-card:hover {
  transform: translateY(-4px);
  border-color: #9f5f91;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.2);
}

.report-card h3 {
  color: #572c57;
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
}

.report-card p {
  margin: 0;
  color: #8a6a8a;
  line-height: 1.5;
}
</style>
