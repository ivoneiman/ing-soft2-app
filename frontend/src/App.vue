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

button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #9f5f91;
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s ease;
}

button:hover {
  background: #572c57;
}

button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
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

h1 {
  font-family: "Anton", sans-serif;
  font-size: 57px;
  margin-bottom: 16px;
}

h2 {
  font-family: "Anton", sans-serif;
  font-size: 35px;
  margin-bottom: 12px;
}

h3 {
  font-family: "Anton", sans-serif;
  font-size: 25px;
  margin-bottom: 10px;
}

h4 {
  font-family: "Anton", sans-serif;
  font-size: 20px;
  margin-bottom: 8px;
}

p, a, button {
  font-family: "Poppins", sans-serif;
  font-size: 20px;
  line-height: 18px;
  letter-spacing: 1.5px;
  font-weight: 300;
  color: #9ca3af;
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
    font-size: 28px;
  }

  h3 {
    font-size: 20px;
  }

  h4 {
    font-size: 16px;
  }

  p, a, button {
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
    font-size: 24px;
  }

  h3 {
    font-size: 18px;
  }

  h4 {
    font-size: 14px;
  }

  p, a, button {
    font-size: 14px;
    line-height: 14px;
    letter-spacing: 0.5px;
  }

  button {
    padding: 8px 12px;
    font-size: 12px;
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
    font-size: 18px;
  }

  h3 {
    font-size: 14px;
  }

  h4 {
    font-size: 12px;
  }

  p, a, button {
    font-size: 12px;
    line-height: 12px;
    letter-spacing: 0px;
  }

  button {
    padding: 6px 10px;
    font-size: 11px;
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