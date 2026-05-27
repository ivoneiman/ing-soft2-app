<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { authStore } from './services/authStore'
import DefaultNavbar from './components/navigation/DefaultNavbar.vue'

onMounted(async () => {
  await authStore.fetchCurrentUser()
})
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #app {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

body {
  font-family: "Bodoni Moda", serif;
  background:  #572c57;  /* ← Sólido en vez de gradiente */
  color:  #f5f5f5; 
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 12px;
  box-sizing: border-box;
}

.error {
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 12px;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  max-width: 420px;
  margin: 60px auto;
  width: 100%;
}

.view {
  color: #f5f5f5;
  background: #572c57;
  min-height: calc(100vh - 140px);
  padding-bottom: 2rem;
}

h1,
h2,
h3,
h4,
h5 {
  font-family: "Anton", sans-serif;
  font-weight: 400;
  line-height: 1.1;
}

h1 {
  font-size: 57px;
  margin-bottom: 16px;
}

h2 {
  font-size: 43px;
  margin-bottom: 12px;
}

h3 {
  font-size: 32px;
  margin-bottom: 10px;
}

h4 {
  font-size: 24px;
  margin-bottom: 8px;
}

h5 {
  font-size: 18px;
  margin-bottom: 6px;
}

p, a {
  font-family: "Poppins", sans-serif;
  font-size: 20px;
  line-height: 18px;
  letter-spacing: 1.5px;
  font-weight: 300;
  color: #9ca3af;
}

button,
.pay-button,
.admin-link {
  border: 2px solid #9f5f91;
  border-radius: 6px;
  background: #9f5f91;
  color: #f6ea98;
  cursor: pointer;
  font-family: "Poppins", sans-serif;
  font-size: 20px;
  font-weight: 700;
  line-height: 18px;
  letter-spacing: 1.5px;
  padding: 12px 16px;
  text-decoration: none;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

button:hover:not(:disabled),
.pay-button:hover:not(:disabled),
.admin-link:hover {
  background: #f6ea98;
  border-color: #f6ea98;
  color: #9f5f91;
}

button:disabled,
.pay-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

a{
  text-decoration: none;
  color: #f6ea98;
}


.anton-regular {
  font-family: "Anton", sans-serif;
  font-weight: 400;
  font-style: normal;
}

.bodoni-moda {
  font-family: "Bodoni Moda", serif;
  font-optical-sizing: auto;
  font-weight: 400;
  font-style: normal;
}

.poppins-regular {
  font-family: "Poppins", sans-serif;
  font-weight: 400;
  font-style: normal;
}

/* ==========================================
   MEDIA QUERIES - RESPONSIVE
   ========================================== */

/* Tablets (1024px y menor) */
@media (max-width: 1024px) {
  h1 {
    font-size: 40px;
  }

  h2 {
    font-size: 32px;
  }

  h3 {
    font-size: 24px;
  }

  h4 {
    font-size: 18px;
  }

  h5 {
    font-size: 15px;
  }

  p, a, button, .pay-button, .admin-link {
    font-size: 16px;
    line-height: 16px;
  }

  .card {
    margin: 40px auto;
    padding: 20px;
  }
}

/* Móviles (768px y menor) */
@media (max-width: 768px) {
  h1 {
    font-size: 32px;
  }

  h2 {
    font-size: 25px;
  }

  h3 {
    font-size: 20px;
  }

  h4 {
    font-size: 16px;
  }

  h5 {
    font-size: 13px;
  }

  p, a, button, .pay-button, .admin-link {
    font-size: 14px;
    line-height: 14px;
    letter-spacing: 0.5px;
  }

  button {
    padding: 10px 14px;
  }

  input {
    padding: 8px;
    font-size: 16px; /* Evita zoom en iOS */
    margin-bottom: 10px;
  }

  .card {
    margin: 24px 12px;
    padding: 16px;
    max-width: 100%;
  }
}

/* Pequeños móviles (480px y menor) */
@media (max-width: 480px) {
  h1 {
    font-size: 24px;
  }

  h2 {
    font-size: 20px;
  }

  h3 {
    font-size: 16px;
  }

  h4 {
    font-size: 14px;
  }

  h5 {
    font-size: 12px;
  }

  p, a, button, .pay-button, .admin-link {
    font-size: 12px;
    line-height: 12px;
    letter-spacing: 0px;
  }

  button {
    padding: 8px 12px;
  }

  input {
    padding: 6px;
  }

  .card {
    margin: 16px 8px;
    padding: 12px;
  }
}

</style>