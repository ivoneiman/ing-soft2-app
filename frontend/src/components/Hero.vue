<template>
  <section class="hero">
    <!-- Overlay -->
    <div class="overlay"></div>

    <!-- Contenido -->
    <div class="hero-content">
      <h1 class="hero-title">
        Tu esfuerzo <br />
        tiene recompensa
      </h1>

      <p class="hero-subtitle">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
        eiusmod tempor incididunt ut labore et dolore magna aliqua.
      </p>

      <div class="hero-buttons">
        <button class="btn-primary">ASOCIATE</button>
        <button class="btn-secondary">ACTIVIDADES</button>
      </div>
    </div>
  </section>
</template>

<script setup>
// ya no necesitás props acá
</script>

<style scoped>
.hero {
  position: relative;
  height: 100vh;
  width: 100%;

  display: flex;
  align-items: center;

  padding-left: 80px;
  padding-top: 100px; /* 🔥 para que no quede debajo del navbar */

  background-image: url('/hero-background.jpg'); 
  background-size: cover;
  background-position: center;
}

/* Overlay violeta */
.overlay {
  position: absolute;
  inset: 0;
  background: rgba(88, 44, 87, 0.65);
  z-index: 1;
}

/* Contenido */
.hero-content {
  position: relative;
  z-index: 2;
  max-width: 600px;
  color: white;
  background-color: transparent;
}

/* Título */
.hero-title {
  font-size: 80px;
  font-weight: 500;
  line-height: 1;
  margin-bottom: 20px;
}

/* Subtítulo */
.hero-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 30px;
}

/* Botones */
.hero-buttons {
  display: flex;
  gap: 16px;
  background-color: transparent;
}

.btn-primary {
  padding: 14px 28px;
  background: #9f5f91;
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:hover {
  background: #8a4f8a;
}

.btn-secondary {
  padding: 24px 28px;
  background: rgba(255, 255, 255, 0.301);
  border: 1px solid transparent;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  font-weight: 600;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>