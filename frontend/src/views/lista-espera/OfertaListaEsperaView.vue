<template>
  <main class="oferta-view">
    <header class="header">
      <div>
        <h1>Tu lugar en la lista de espera</h1>
        <p>Se liberó un cupo y fuiste seleccionado/a. Decidí qué hacer con tu lugar.</p>
      </div>
      <router-link to="/" class="back-button">Volver al Inicio</router-link>
    </header>

    <div v-if="isLoading" class="empty-state">Cargando tu oferta...</div>

    <div v-else-if="declined" class="empty-state success">
      Liberaste tu lugar. Se lo ofrecimos a la siguiente persona en la lista de espera.
    </div>

    <div v-else-if="!offer" class="empty-state">
      Esta oferta ya no está disponible (puede que ya se haya pagado, cancelado o vencido).
      <div class="empty-actions">
        <router-link to="/pagos">Ver mis pagos pendientes</router-link>
        <router-link to="/actividades">Ver actividades</router-link>
      </div>
    </div>

    <section v-else class="offer-card">
      <div class="card-header">
        <h2>{{ offer.actividad }}</h2>
        <span class="status-pill pending">Pendiente de decisión</span>
      </div>

      <dl class="offer-details">
        <div>
          <dt>Fecha y hora</dt>
          <dd>{{ formatDateTime(offer.fecha_hora) }}</dd>
        </div>
        <div>
          <dt>Tipo de reserva</dt>
          <dd>{{ offer.tipo }}</dd>
        </div>
        <div>
          <dt>Monto a pagar</dt>
          <dd>{{ formatMoney(offer.final_amount ?? offer.amount) }}</dd>
        </div>
      </dl>

      <p class="explanation">
        Estabas anotado/a en la lista de espera de esta clase y se liberó un cupo para vos.
        Si querés confirmarlo, hacé click en <strong>"Inscribirse"</strong> para ir a pagar.
        Si en realidad ya no te interesa, hacé click en <strong>"Arrepentirse"</strong> para
        liberar el lugar y que se lo ofrezcamos a la siguiente persona en la lista de espera.
      </p>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

      <div class="offer-actions">
        <button class="enroll-button" @click="enrollNow" :disabled="isSubmitting">
          {{ isSubmitting === 'enroll' ? 'Redirigiendo a Mercado Pago...' : 'Inscribirse' }}
        </button>
        <button class="regret-button" @click="confirmRegret" :disabled="isSubmitting">
          {{ isSubmitting === 'regret' ? 'Liberando lugar...' : 'Arrepentirse' }}
        </button>
      </div>
    </section>

    <div v-if="showConfirmModal" class="modal-backdrop" @click.self="showConfirmModal = false">
      <div class="modal">
        <h2>Confirmar</h2>
        <p>
          ¿Seguro que querés liberar tu lugar en <strong>{{ offer?.actividad }}</strong>?
          Esta acción no se puede deshacer: el cupo pasará a la siguiente persona en la lista
          de espera.
        </p>
        <div class="modal-actions">
          <button class="secondary-button" @click="showConfirmModal = false">Cerrar</button>
          <button class="danger-button" @click="regretNow">Sí, liberar mi lugar</button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getPendingEnrollments, createPayment, declineWaitlistOffer } from '../../services/api';
import { formatDateTime, formatMoney } from '../../utils/formatters';

const route = useRoute();

const isLoading = ref(true);
const isSubmitting = ref(null);
const offer = ref(null);
const declined = ref(false);
const errorMessage = ref('');
const showConfirmModal = ref(false);

async function loadOffer() {
  isLoading.value = true;
  try {
    const response = await getPendingEnrollments();
    const enrollments = response.data.enrollments || [];
    const enrollmentId = String(route.params.enrollmentId);
    offer.value = enrollments.find((e) => String(e.id) === enrollmentId && e.waitlist_offer) || null;
  } catch (err) {
    console.error('Error cargando la oferta de lista de espera:', err);
    offer.value = null;
  } finally {
    isLoading.value = false;
  }
}

async function enrollNow() {
  if (!offer.value) return;
  errorMessage.value = '';
  isSubmitting.value = 'enroll';
  try {
    const response = await createPayment({
      enrollment_id: offer.value.id,
      payment_method: 'mercado_pago',
      payment_type: 'full',
    });
    window.location.href = response.data.init_point;
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error al generar el link de pago';
    isSubmitting.value = null;
  }
}

function confirmRegret() {
  showConfirmModal.value = true;
}

async function regretNow() {
  if (!offer.value) return;
  showConfirmModal.value = false;
  errorMessage.value = '';
  isSubmitting.value = 'regret';
  try {
    await declineWaitlistOffer(offer.value.id);
    declined.value = true;
    offer.value = null;
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error al liberar el lugar';
  } finally {
    isSubmitting.value = null;
  }
}

onMounted(() => { loadOffer(); });
</script>

<style scoped>
.oferta-view { padding: 24px; max-width: 700px; margin: 0 auto; min-height: calc(100vh - 140px); }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; gap: 1rem; }
.header h1 { color: #fff; margin: 0 0 0.5rem 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
.header p { color: #e0c0e0; margin: 0; font-size: 1.05rem; }
.back-button { background: #f6ea98; padding: 10px 16px; border-radius: 8px; color: #572c57; text-decoration: none; font-weight: 700; white-space: nowrap; }

.empty-state { background: #fff; padding: 2rem; text-align: center; border-radius: 12px; color: #8a6a8a; border: 2px solid #d0c0d0; }
.empty-state.success { color: #027a48; border-color: #12b76a; background: #ecfdf3; }
.empty-actions { display: flex; justify-content: center; gap: 1.5rem; margin-top: 1rem; }
.empty-actions a { color: #572c57; font-weight: 700; }

.offer-card { background: #fff; border: 2px solid #e8dce8; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.card-header h2 { margin: 0; color: #572c57; }
.status-pill { padding: 4px 12px; border-radius: 999px; font-size: 0.85rem; font-weight: 700; }
.status-pill.pending { background: #fef3c7; color: #92400e; }

.offer-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.offer-details dt { font-size: 0.85rem; color: #8a6a8a; margin-bottom: 0.25rem; }
.offer-details dd { margin: 0; font-weight: 700; color: #333; }

.explanation { color: #555; line-height: 1.5; margin-bottom: 1.5rem; }
.error-message { color: #b91c1c; background: #fee2e2; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; }

.offer-actions { display: flex; gap: 1rem; flex-wrap: wrap; }
.enroll-button { background: #12b76a; color: #fff; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; cursor: pointer; }
.enroll-button:disabled { opacity: 0.6; cursor: not-allowed; }
.regret-button { background: transparent; border: 2px solid #b91c1c; color: #b91c1c; padding: 12px 24px; border-radius: 8px; font-weight: 700; cursor: pointer; }
.regret-button:disabled { opacity: 0.6; cursor: not-allowed; }

.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border-radius: 12px; padding: 1.5rem; max-width: 420px; width: 90%; }
.modal h2 { margin-top: 0; color: #572c57; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
.secondary-button { background: #f0e6f0; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; color: #572c57; }
.danger-button { background: #b91c1c; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; }
</style>
