<template>
  <div class="scan-qr-view">
    <div class="scan-layout">
      <section class="scanner-panel">
        <h2>Pasar asistencia</h2>
        <section v-if="selectedClass" class="selected-class">
          <span>Clase seleccionada</span>
          <h3>{{ selectedClass.actividad || selectedClass.name }}</h3>
          <p>{{ formatClassDate(selectedClass.fecha_hora) }} · {{ selectedClass.time || formatClassTime(selectedClass.fecha_hora) }} hs</p>
        </section>

        <div class="scanner-stage">
          <div v-if="canScan" id="qr-reader" ref="qrReaderElement"></div>
          <div v-else class="scanner-placeholder">
            {{ loadingClass ? 'Cargando clase...' : 'Seleccioná una clase válida para tomar asistencia.' }}
          </div>

          <Transition name="scanner-feedback">
            <div
              v-if="scannerFeedback"
              :class="['scanner-feedback', scannerFeedback.type]"
              role="status"
              aria-live="polite"
            >
              <span class="scanner-feedback-icon" aria-hidden="true">{{ scannerFeedback.icon }}</span>
              <span>{{ scannerFeedback.message }}</span>
            </div>
          </Transition>
        </div>
      </section>

      <section class="attendance-panel">
        <div class="attendance-header">
          <div>
            <span>En tiempo real</span>
            <h2>Lista de asistencia</h2>
          </div>
          <button type="button" :disabled="loadingAttendance || !classId" @click="loadAttendance">
            {{ loadingAttendance ? 'Actualizando...' : 'Actualizar' }}
          </button>
        </div>

        <div class="attendance-summary">
          <div>
            <strong>{{ attendanceSummary.present }}</strong>
            <span>Presentes</span>
          </div>
          <div>
            <strong>{{ attendanceSummary.pending }}</strong>
            <span>Pendientes</span>
          </div>
          <div>
            <strong>{{ attendanceSummary.paid_enrollments }}</strong>
            <span>Inscriptos pagos</span>
          </div>
        </div>

        <p v-if="attendanceError" class="attendance-error">{{ attendanceError }}</p>
        <p v-else-if="loadingAttendance" class="attendance-empty">Cargando asistencias...</p>
        <p v-else-if="attendanceRoster.length === 0" class="attendance-empty">
          No hay inscriptos pagos para esta clase.
        </p>

        <ul v-else class="attendance-list">
          <li v-for="person in attendanceRoster" :key="person.user_id">
            <div>
              <strong>{{ person.apellido || '' }} {{ person.username }}</strong>
              <span>{{ person.email }}</span>
            </div>
            <span :class="['attendance-status', person.present ? 'present' : 'pending']">
              {{ person.present ? 'Presente' : 'Pendiente' }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, onMounted, onBeforeUnmount } from 'vue';
import { Html5Qrcode } from 'html5-qrcode';
import { getAllClasses, getClassAttendance, registerAttendance } from '@/services/api';
import { useRoute } from 'vue-router';
import { CLASS_STATUS } from '@/constants/statuses';
import { formatShortDate } from '@/utils/formatters';
import { parseUserQr } from '@/utils/qrAttendance';

const route = useRoute();
const qrReaderElement = ref(null);
const errorMessage = ref('');
const successMessage = ref('');
const isScanning = ref(false);
const loadingClass = ref(true);
const selectedClass = ref(null);
const loadingAttendance = ref(false);
const attendanceError = ref('');
const attendanceRoster = ref([]);
const attendanceSummary = ref({
  present: 0,
  pending: 0,
  paid_enrollments: 0,
});
let html5QrcodeScanner = null;
let feedbackTimeoutId = null;

const classId = computed(() => {
  const parsedClassId = Number(route.params.classId);
  return Number.isInteger(parsedClassId) && parsedClassId > 0 ? parsedClassId : null;
});

const canScan = computed(() => Boolean(classId.value && selectedClass.value && !loadingClass.value));

const scannerFeedback = computed(() => {
  if (successMessage.value) {
    return {
      icon: '✓',
      message: successMessage.value,
      type: 'success',
    };
  }

  if (!errorMessage.value) return null;

  const isAlreadyRegistered = errorMessage.value.toLowerCase().includes('asistencia ya registrada');

  return {
    icon: isAlreadyRegistered ? '!' : 'i',
    message: errorMessage.value,
    type: isAlreadyRegistered ? 'warning' : 'error',
  };
});

function clearFeedbackTimer() {
  if (feedbackTimeoutId) {
    clearTimeout(feedbackTimeoutId);
    feedbackTimeoutId = null;
  }
}

function scheduleFeedbackClear({ unlockScanner = false } = {}) {
  clearFeedbackTimer();
  feedbackTimeoutId = setTimeout(() => {
    errorMessage.value = '';
    successMessage.value = '';
    if (unlockScanner) {
      isScanning.value = false;
    }
    feedbackTimeoutId = null;
  }, 3000);
}

const onScanSuccess = async (decodedText) => {
  if (isScanning.value) return;
  isScanning.value = true;
  clearFeedbackTimer();
  errorMessage.value = '';
  successMessage.value = '';

  try {
    if (!classId.value || !selectedClass.value) {
      errorMessage.value = 'No hay una clase válida seleccionada para registrar asistencia.';
      isScanning.value = false;
      scheduleFeedbackClear();
      return;
    }

    const userId = parseUserQr(decodedText);
    if (!userId) {
      errorMessage.value = 'QR no válido. Formato esperado: USER:<id>';
      isScanning.value = false;
      scheduleFeedbackClear();
      return;
    }

    await registerAttendance({ user_id: userId, class_id: classId.value });
    successMessage.value = `Asistencia registrada con éxito para usuario ${userId}`;
    errorMessage.value = '';
    await loadAttendance();

    scheduleFeedbackClear({ unlockScanner: true });
  } catch (error) {
    errorMessage.value = error.response?.status === 404
      ? 'QR no válido. El usuario no pertenece al sistema.'
      : error.response?.data?.error || 'Error al registrar asistencia';
    isScanning.value = false;
    scheduleFeedbackClear();
  }
};

const onScanFailure = (error) => {
  console.debug('QR scan error:', error);
};

async function loadSelectedClass() {
  loadingClass.value = true;
  selectedClass.value = null;
  errorMessage.value = '';

  try {
    if (!classId.value) {
      errorMessage.value = 'No se indicó una clase válida para tomar asistencia.';
      return;
    }

    const response = await getAllClasses();
    const foundClass = (response.data.classes || []).find((clase) => clase.id === classId.value);
    if (!foundClass) {
      errorMessage.value = 'La clase seleccionada no existe.';
      return;
    }
    if (foundClass.estado !== CLASS_STATUS.ACTIVE) {
      errorMessage.value = 'No se puede tomar asistencia sobre una clase cancelada.';
      return;
    }

    selectedClass.value = foundClass;
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'No se pudo cargar la clase seleccionada.';
  } finally {
    loadingClass.value = false;
  }
}

async function startScanner() {
  if (!canScan.value) return;

  try {
    await nextTick();
    if (!qrReaderElement.value) {
      errorMessage.value = 'Error: elemento de cámara no encontrado en el DOM';
      return;
    }

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
    errorMessage.value = 'No se pudo inicar la cámara, verifque los permisos de su navegador';
    console.error('Camera initialization error:', err);
  }
}

async function loadAttendance() {
  if (!classId.value) return;

  loadingAttendance.value = true;
  attendanceError.value = '';

  try {
    const response = await getClassAttendance(classId.value);
    attendanceRoster.value = response.data.roster || [];
    attendanceSummary.value = response.data.summary || {
      present: 0,
      pending: 0,
      paid_enrollments: 0,
    };
  } catch (error) {
    attendanceError.value = error.response?.data?.error || 'No se pudo cargar la lista de asistencia.';
  } finally {
    loadingAttendance.value = false;
  }
}

function formatClassDate(value) {
  return formatShortDate(value);
}

function formatClassTime(value) {
  if (!value) return '-';

  return new Intl.DateTimeFormat('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

onMounted(async () => {
  await loadSelectedClass();
  await loadAttendance();
  await startScanner();
});

onBeforeUnmount(async () => {
  clearFeedbackTimer();

  if (html5QrcodeScanner) {
    try {
      await html5QrcodeScanner.stop();
      await html5QrcodeScanner.clear();
    } catch (err) {
      console.error('Error al limpiar QR scanner:', err);
    } finally {
      html5QrcodeScanner = null;
    }
  }
});
</script>

<style scoped>
.scan-qr-view {
  margin-top: 2rem;
  width: 100%;
}

.scan-layout {
  align-items: flex-start;
  display: grid;
  gap: 24px;
  grid-template-columns: minmax(320px, 500px) minmax(320px, 520px);
  justify-content: center;
  padding: 0 20px;
}

.scanner-panel {
  align-items: center;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.selected-class,
.scanner-placeholder {
  width: 100%;
}

.selected-class {
  background: #572c57;
  border: 1px solid #9f5f91;
  border-radius: 8px;
  color: #f5f5f5;
  margin-bottom: 1rem;
  padding: 1rem;
}

.selected-class span {
  color: #f6ea98;
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
  text-transform: uppercase;
}

.selected-class h3,
.selected-class p {
  margin: 0;
}

.selected-class p {
  color: #e5d8eb;
  margin-top: 0.35rem;
}

.scanner-placeholder {
  align-items: center;
  background: #1f1b24;
  border: 2px dashed #9f5f91;
  border-radius: 8px;
  color: #f5f5f5;
  display: flex;
  min-height: 220px;
  justify-content: center;
  padding: 1rem;
  text-align: center;
}

.scanner-stage {
  max-width: 500px;
  position: relative;
  width: 100%;
}

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

.scanner-feedback {
  align-items: center;
  border: 2px solid transparent;
  border-radius: 8px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
  display: flex;
  gap: 12px;
  left: 50%;
  max-width: calc(100% - 32px);
  min-height: 72px;
  padding: 16px 18px;
  position: absolute;
  text-align: left;
  top: 22px;
  transform: translateX(-50%);
  width: 430px;
  z-index: 5;
}

.scanner-feedback span:last-child {
  font-size: 1.12rem;
  font-weight: 800;
  line-height: 1.25;
}

.scanner-feedback-icon {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 1.45rem;
  font-weight: 900;
  height: 38px;
  justify-content: center;
  line-height: 1;
  width: 38px;
}

.scanner-feedback.warning {
  background: #ffedd5;
  border-color: #f59e0b;
  color: #7c2d12;
}

.scanner-feedback.warning .scanner-feedback-icon {
  background: #f59e0b;
  color: #fff7ed;
}

.scanner-feedback.error {
  background: #fee2e2;
  border-color: #ef4444;
  color: #7f1d1d;
}

.scanner-feedback.error .scanner-feedback-icon {
  background: #dc2626;
  color: #fff;
}

.scanner-feedback.success {
  background: #dcfce7;
  border-color: #22c55e;
  color: #14532d;
}

.scanner-feedback.success .scanner-feedback-icon {
  background: #16a34a;
  color: #fff;
}

.scanner-feedback-enter-active,
.scanner-feedback-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.scanner-feedback-enter-from,
.scanner-feedback-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px) scale(0.98);
}

.attendance-panel {
  background: #572c57;
  border: 1px solid #9f5f91;
  border-radius: 8px;
  color: #f5f5f5;
  padding: 18px;
  width: 100%;
}

.attendance-header {
  align-items: center;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  margin-bottom: 16px;
}

.attendance-header span {
  color: #f6ea98;
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
  text-transform: uppercase;
}

.attendance-header h2 {
  margin: 0;
}

.attendance-header button {
  font-size: 13px;
  white-space: nowrap;
}

.attendance-summary {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 16px;
}

.attendance-summary div {
  background: rgba(245, 245, 245, 0.08);
  border: 1px solid #9f5f91;
  border-radius: 8px;
  padding: 12px;
}

.attendance-summary strong,
.attendance-summary span {
  display: block;
}

.attendance-summary strong {
  color: #f6ea98;
  font-size: 1.5rem;
}

.attendance-summary span {
  color: #e5d8eb;
  font-size: 0.8rem;
}

.attendance-list {
  display: grid;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.attendance-list li {
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  display: flex;
  gap: 12px;
  justify-content: space-between;
  padding: 12px;
}

.attendance-list strong,
.attendance-list span {
  display: block;
}

.attendance-list div span {
  color: #d9cfe0;
  font-size: 0.85rem;
  margin-top: 3px;
}

.attendance-status {
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 6px 10px;
  text-align: center;
  white-space: nowrap;
}

.attendance-status.present {
  background: #d1fae5;
  color: #065f46;
}

.attendance-status.pending {
  background: #fee2e2;
  color: #991b1b;
}

.attendance-empty,
.attendance-error {
  border-radius: 6px;
  margin: 0;
  padding: 16px;
  text-align: center;
}

.attendance-empty {
  border: 1px dashed #9f5f91;
  color: #d9cfe0;
}

.attendance-error {
  background: #fee2e2;
  color: #991b1b;
}

@media (max-width: 940px) {
  .scan-layout {
    grid-template-columns: minmax(0, 500px);
  }
}

@media (max-width: 560px) {
  .scan-layout {
    padding: 0 12px;
  }

  .attendance-header,
  .attendance-list li {
    align-items: stretch;
    flex-direction: column;
  }

  .attendance-header button {
    width: 100%;
  }

  .attendance-summary {
    grid-template-columns: 1fr;
  }
}
</style>
