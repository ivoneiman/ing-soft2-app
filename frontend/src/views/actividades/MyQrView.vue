<template>
  <div class="my-qr-view">
    <h2>Mi QR</h2>
    <div v-if="userId">
      <qrcode-vue :value="qrValue" :size="200" />
    </div>
    <div v-else>
      <p>Cargando datos del usuario...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getCurrentUser } from '@/services/api';
import QrcodeVue from 'qrcode.vue';

const userId = ref(null);
const qrValue = ref('');

onMounted(async () => {
  try {
    const response = await getCurrentUser();
    const user = response.data.user;
    userId.value = user.id;
    qrValue.value = `USER:${user.id}`;
  } catch (e) {
    console.error('Error obteniendo usuario', e);
  }
});
</script>

<style scoped>
.my-qr-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 2rem;
}
</style>
