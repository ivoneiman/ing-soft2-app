<template>
  <div class="admin-view">
    <header class="admin-header">
      <h1>Gestión de Profesores</h1>
      <p class="lead">Seleccioná una opción para administrar los profesores del sistema.</p>
    </header>

    <div class="admin-card">
      <div class="options-grid">
        <RouterLink to="/admin/profesores/crear" class="option-card">
          <h2 class="option-title">Cargar Profesor</h2>
          <p class="option-description">Agregar un nuevo profesor al sistema.</p>
        </RouterLink>

        <RouterLink to="/admin/profesores/listar" class="option-card">
          <h2 class="option-title">Listar Profesores</h2>
          <p class="option-description">Ver y gestionar la lista de profesores existentes.</p>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router';
</script>

<style scoped>
.admin-view {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
  min-height: calc(100vh - 140px);
}

.admin-header h1 {
  color: #fff;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.lead {
  color: #e0c0e0;
  margin-bottom: 2rem;
  font-size: 1.05rem;
  font-weight: 500;
}

.admin-card {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.option-card {
  display: block;
  padding: 1.5rem;
  border: 2px solid #e8dce8;
  border-radius: 12px;
  text-align: center;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s ease;
}

.option-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 20px rgba(87, 44, 87, 0.15);
  border-color: #9f5f91;
}

.option-title {
  color: #572c57;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.option-description {
  color: #6b7280;
  font-size: 0.95rem;
}
</style>