<template>
  <div class="configuracion-view">
    <h1>Configuración</h1>
    <p class="subtitle">Opciones del sistema</p>

    <div class="config-actions">
      <router-link to="/configuracion/notificacion" class="admin-link small-button">
        Configuración de notificación
      </router-link>
    </div>
  </div>
</template>

<script setup>
// Lógica de la vista de configuración puede añadirse aquí.
</script>

<style scoped>
.configuracion-view {
  padding: 24px;
  min-height: 100%;
}

.subtitle {
  color: #6b5d7b;
  margin-bottom: 1.5rem;
}

.config-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  max-width: 760px;
}

.action-copy {
  flex: 1 1 320px;
}

.action-copy h2 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
}

.action-copy p {
  margin: 0;
  color: rgba(245, 245, 245, 0.85);
}

.small-button {
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 6px;
  min-width: 220px;
  display: inline-flex;
  justify-content: center;
}
</style>
