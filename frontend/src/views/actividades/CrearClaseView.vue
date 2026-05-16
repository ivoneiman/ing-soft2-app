<template>
  <div class="view">
    <h1>Crear Clase</h1>
    <p>Seleccione una fecha para crear la clase.</p>
    <Calendario />
  </div>
</template>

<script setup>
import Calendario from "@/components/calendario/calendario.vue";
</script>

<style scoped>
.view {
  padding: 24px;
}
</style>