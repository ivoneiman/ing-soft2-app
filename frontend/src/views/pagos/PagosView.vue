<template>
  <div class="pagos-view">
    <h1>Página de Pagos</h1>
    <p>Contenido de la página de pagos (por implementar).</p>

    <!-- Botón para acceder a la configuración de descuentos, solo visible para admins -->
    <div v-if="isAdmin" class="admin-section">
      <h2>Panel de Administrador</h2>
      <p>Desde aquí puedes gestionar las promociones y descuentos de las clases.</p>
      <RouterLink to="/admin/descuentos" class="btn-admin">
        Configurar Descuentos
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { RouterLink } from 'vue-router';
import { roleHelpers } from '../../utils/roleHelpers';

// Verificamos si el usuario actual es administrador para mostrar el botón
const isAdmin = ref(roleHelpers.isAdmin());
</script>

<style scoped>
.pagos-view {
  padding: 20px;
}

.admin-section {
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid #4a5568;
  border-radius: 8px;
  background-color: rgba(0,0,0,0.2);
}

.btn-admin {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: #4f46e5;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  font-weight: bold;
  transition: background-color 0.2s;
}

.btn-admin:hover {
  background-color: #4338ca;
}
</style>
