<template>
  <div id="app">
    <DefaultNavbar />
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { authStore } from './services/authStore'
import DefaultNavbar from './components/DefaultNavbar.vue'

onMounted(async () => {
  await authStore.fetchCurrentUser()
})
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Bodoni Moda"; background: #f5f5f5; color: #572c57; }
button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #9f5f91;
  color: white;
  cursor: pointer;
  font-size: 14px;
}
button:hover { background: #572c57; }
button:disabled { background: #9ca3af; cursor: not-allowed; }
input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 12px;
}
.error { color: #dc2626; font-size: 14px; margin-bottom: 12px; }
.card {
  background: white;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  max-width: 420px;
  margin: 60px auto;
}
div{
  color: #f5f5f5;
  background: #572c57;
}
h1{
  font-family: "Anton"; font-size: 57px;
}
h2{
  font-family: "Anton"; font-size: 35px;
}
h3{
  font-family: "Anton"; font-size: 25px;
}
h4{
  font-family: "Anton";  font-size: 20px;
}
p,a,button{
    font-family: Poppins, sans-serif; font-size: 20px; line-height: 12px; letter-spacing: 1.5px; font-weight: regular; color: #fff
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


</style>
