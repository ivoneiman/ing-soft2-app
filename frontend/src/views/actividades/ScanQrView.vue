<template>
  <div class="scan-qr-view">
    <h2>Pasar asistencia</h2>
    <div id="qr-reader" ref="qrReaderElement"></div>
    <div v-if="errorMessage" class="error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="success">{{ successMessage }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Html5Qrcode } from 'html5-qrcode';
import { registerAttendance } from '@/services/api';
import { useRoute } from 'vue-router';

const route = useRoute();
const qrReaderElement = ref(null);
const errorMessage = ref('');
const successMessage = ref('');
const isScanning = ref(false);
let html5QrcodeScanner = null;

const onScanSuccess = async (decodedText) => {
  // Bloquear múltiples scans simultáneos
  if (isScanning.value) return;
  isScanning.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    // Validar formato USER:<id>
    const match = decodedText.match(/^USER:(\d+)$/);
    if (!match) {
      errorMessage.value = 'QR no válido. Formato esperado: USER:<id>';
      isScanning.value = false;
      return;
    }

    const userId = parseInt(match[1]);
    // Obtener class_id de route params o usar valor por defecto
    const classId = parseInt(route.params.classId) || 1;

    // Registrar asistencia
    await registerAttendance({ user_id: userId, class_id: classId });
    successMessage.value = `Asistencia registrada con éxito para usuario ${userId}`;
    errorMessage.value = '';

    // Limpiar mensaje después de 3 segundos
    setTimeout(() => {
      successMessage.value = '';
      isScanning.value = false;
    }, 3000);
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Error al registrar asistencia';
    isScanning.value = false;
  }
};

const onScanFailure = (error) => {
  // html5-qrcode puede generar errores frecuentemente, no necesitamos mostrarlos todos
  console.debug('QR scan error:', error);
};

onMounted(async () => {
  try {
    html5QrcodeScanner = new Html5Qrcode('qr-reader');

    const config = {
      fps: 10,
      qrbox: { width: 250, height: 250 },
      aspectRatio: 1.0,
    };

    await html5QrcodeScanner.start(
      { facingMode: 'environment' },
      config,
      onScanSuccess,
      onScanFailure
    );
  } catch (err) {
    errorMessage.value = 'No se pudo inicializar la cámara: ' + err.message;
    console.error('Camera initialization error:', err);
  }
});

onBeforeUnmount(async () => {
  if (html5QrcodeScanner) {
    try {
      // Detener la cámara y liberar recursos
      await html5QrcodeScanner.stop();
      // Limpiar el elemento del DOM completamente
      await html5QrcodeScanner.clear();
    } catch (err) {
      console.error('Error al limpiar QR scanner:', err);
    } finally {
      // Asegurar que se libera la referencia
      html5QrcodeScanner = null;
    }
  }
});
</script>

<style scoped>
.scan-qr-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 2rem;
  width: 100%;
}

/* Contenedor del scanner QR */
#qr-reader {
  width: 100%;
  max-width: 500px;
  height: 500px;
  border: 2px solid #ccc;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
  position: relative;
  display: block;
}

/* Video stream dentro del scanner */
:deep(#qr-reader video) {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: center;
}

/* Canvas para el escaneo */
:deep(#qr-reader canvas) {
  width: 100%;
  height: 100%;
  display: block;
}

/* Elementos internos sin estilos globales */
:deep(#qr-reader *) {
  background: transparent !important;
  color: inherit !important;
}

.error {
  color: #d32f2f;
  margin-top: 1rem;
  padding: 0.5rem;
  background-color: #ffebee;
  border-radius: 4px;
  font-weight: 500;
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.success {
  color: #388e3c;
  margin-top: 1rem;
  padding: 0.5rem;
  background-color: #e8f5e9;
  border-radius: 4px;
  font-weight: 500;
  width: 100%;
  max-width: 500px;
  text-align: center;
}
</style>
