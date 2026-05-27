<template>
  <main class="payments-view">
    <header class="payments-header">
      <div>
        <h1>Pagos</h1>
        <p>Inscripciones pendientes e historial de pagos.</p>
      </div>

      <RouterLink v-if="isAdmin" to="/admin/descuentos" class="admin-link">
        Configurar descuentos
      </RouterLink>
    </header>

    <p v-if="returnMessage" :class="['return-message', returnMessage.type]">
      {{ returnMessage.text }}
    </p>

    <nav class="payments-tabs" aria-label="Secciones de pagos">
      <button type="button" :class="{ active: activeTab === PAYMENT_TAB.PENDING }" @click="activeTab = PAYMENT_TAB.PENDING">
        Inscripciones pendientes
      </button>
      <button type="button" :class="{ active: activeTab === PAYMENT_TAB.HISTORY }" @click="activeTab = PAYMENT_TAB.HISTORY">
        Historial de pagos
      </button>
      <button type="button" :class="{ active: activeTab === PAYMENT_TAB.CREDITS }" @click="activeTab = PAYMENT_TAB.CREDITS">
        Créditos
      </button>
      <button type="button" :class="{ active: activeTab === PAYMENT_TAB.NOTIFICATIONS }" @click="activeTab = PAYMENT_TAB.NOTIFICATIONS">
        Notificaciones
      </button>
    </nav>

    <fieldset v-if="isDiscountTestVisible && activeTab === PAYMENT_TAB.PENDING" class="discount-test-mode">
      <p>Modo testing descuentos</p>
      <label v-for="option in discountTestOptions" :key="option.value">
        <input v-model="discountTestDay" type="radio" name="discount-test-day" :value="option.value" />
        <span>{{ option.label }}</span>
      </label>
    </fieldset>

    <section v-if="activeTab === PAYMENT_TAB.PENDING" class="pending-section">
      <div v-if="isLoadingEnrollments" class="empty-state">Cargando inscripciones...</div>
      <div v-else-if="pendingEnrollments.length === 0" class="empty-state">
        No tenés inscripciones pendientes de pago.
      </div>

      <template v-else>
        <article
          v-for="enrollment in pendingEnrollments"
          :key="enrollment.id"
          :class="['enrollment-card', { highlighted: String(route.query.enrollment_id) === String(enrollment.id) }]"
        >
          <div class="enrollment-main">
            <div>
              <p class="eyebrow">{{ enrollment.actividad || enrollment.class_name }}</p>
              <h2>{{ enrollment.class_name }}</h2>
            </div>
            <span class="status-pill">{{ enrollmentStatusLabel(enrollment.estado) }}</span>
          </div>

          <dl class="enrollment-details">
            <div>
              <dt>Fecha y hora</dt>
              <dd>{{ formatDateTime(enrollment.fecha_hora) }}</dd>
            </div>
            <div>
              <dt>Vencimiento</dt>
              <dd>{{ formatDateTime(enrollment.expires_at) }}</dd>
            </div>
            <div>
              <dt>Descuento aplicado</dt>
              <dd>{{ Number(enrollment.discount_percentage || 0) }}%</dd>
            </div>
            <div>
              <dt>Monto</dt>
              <dd>{{ formatMoney(enrollment.final_amount) }}</dd>
            </div>
          </dl>

          <section class="payment-summary">
            <h3>Resumen</h3>
            <dl>
              <div>
                <dt>Precio original</dt>
                <dd>{{ formatMoney(enrollment.amount) }}</dd>
              </div>
              <div>
                <dt>Total a pagar</dt>
                <dd>{{ formatMoney(enrollment.final_amount) }}</dd>
              </div>
            </dl>
          </section>

          <button
            class="pay-button"
            type="button"
            :disabled="isSubmittingId === enrollment.id || !enrollment.is_payable"
            @click="payNow(enrollment)"
          >
            {{ isSubmittingId === enrollment.id ? 'Redirigiendo...' : 'Pagar ahora' }}
          </button>
        </article>
      </template>
    </section>

    <section v-else-if="activeTab === PAYMENT_TAB.HISTORY" class="history-section">
      <h2>Historial de pagos</h2>

      <div v-if="isLoadingHistory" class="empty-state">Cargando pagos...</div>
      <div v-else-if="payments.length === 0" class="empty-state">Todavía no hay pagos registrados.</div>

      <table v-else class="payments-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Actividad</th>
            <th>Método</th>
            <th>Original</th>
            <th>Descuento</th>
            <th>Total</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in payments" :key="payment.id">
            <td>{{ formatDateTime(payment.created_at) }}</td>
            <td>{{ payment.actividad || payment.class_name || '-' }}</td>
            <td>{{ paymentMethodLabel(payment.payment_method) }}</td>
            <td>{{ formatMoney(payment.amount) }}</td>
            <td>{{ Number(payment.discount_percentage || 0) }}%</td>
            <td>{{ formatMoney(payment.final_amount) }}</td>
            <td>{{ paymentStatusLabel(payment.status) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-else-if="activeTab === PAYMENT_TAB.CREDITS" class="history-section">
      <h2>Créditos disponibles</h2>

      <div v-if="isLoadingCredits" class="empty-state">Cargando créditos...</div>
      <div v-else-if="credits.length === 0" class="empty-state">Todavía no tenés créditos registrados.</div>

      <table v-else class="payments-table">
        <thead>
          <tr>
            <th>Actividad</th>
            <th>Vencimiento</th>
            <th>Origen</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="credit in credits" :key="credit.id">
            <td>{{ credit.actividad_name || '-' }}</td>
            <td>{{ formatDateTime(credit.expires_at || credit.fecha_expiracion) }}</td>
            <td>{{ credit.origin_class_name || '-' }}</td>
            <td>{{ creditStatusLabel(credit.status) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-else class="history-section">
      <h2>Notificaciones</h2>

      <div v-if="isLoadingNotifications" class="empty-state">Cargando notificaciones...</div>
      <div v-else-if="notifications.length === 0" class="empty-state">No tenés notificaciones.</div>

      <div v-else class="notifications-list">
        <article v-for="notification in notifications" :key="notification.id" class="notification-item">
          <div>
            <h3>{{ notification.title }}</h3>
            <p>{{ notification.message }}</p>
          </div>
          <time>{{ formatDateTime(notification.created_at) }}</time>
        </article>
      </div>
    </section>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { PAYMENT_METHOD, statusLabel } from '../../constants/statuses';
import { PAYMENT_RETURN_MESSAGES, PAYMENT_RETURN_STATUS, PAYMENT_TAB, PAYMENT_TABS } from '../../constants/payments';
import {
  createPayment,
  getMyCredits,
  getMyNotifications,
  getPaymentDiscountRules,
  getPaymentHistory,
  getPendingEnrollments,
} from '../../services/api';
import { formatDateTime, formatMoney } from '../../utils/formatters';
import { roleHelpers } from '../../utils/roleHelpers';

const route = useRoute();
const isAdmin = ref(roleHelpers.isAdmin());
const activeTab = ref(PAYMENT_TABS.includes(route.query.tab) ? route.query.tab : PAYMENT_TAB.PENDING);
const isSubmittingId = ref(null);
const isLoadingEnrollments = ref(false);
const isLoadingHistory = ref(false);
const isLoadingCredits = ref(false);
const isLoadingNotifications = ref(false);
const errorMessage = ref('');
const pendingEnrollments = ref([]);
const payments = ref([]);
const credits = ref([]);
const notifications = ref([]);
const discountTestDay = ref('');
const discountRules = ref({ periods: [] });
const isDiscountTestVisible = import.meta.env.DEV || import.meta.env.MODE === 'test';

const discountTestOptions = computed(() => {
  const options = [{ value: '', label: 'Fecha real' }];
  const sampleDaysByPercentage = { 0: '10', 40: '17', 70: '25' };

  discountRules.value.periods.forEach((period) => {
    const value = sampleDaysByPercentage[period.percentage];
    if (value) options.push({ value, label: `Simular día ${value} (${period.percentage}%)` });
  });

  return options;
});

const returnMessage = computed(() => {
  if (PAYMENT_RETURN_MESSAGES[route.query.status]) return PAYMENT_RETURN_MESSAGES[route.query.status];
  if (route.query.status === PAYMENT_RETURN_STATUS.FAILURE) return { type: 'failure', text: route.query.message || 'Pago rechazado' };
  return null;
});

function enrollmentStatusLabel(status) {
  return statusLabel('enrollment', status);
}

function paymentMethodLabel(paymentMethod) {
  return statusLabel('paymentMethod', paymentMethod);
}

function paymentStatusLabel(status) {
  return statusLabel('payment', status);
}

function creditStatusLabel(status) {
  return statusLabel('credit', status);
}

async function loadPendingEnrollments() {
  isLoadingEnrollments.value = true;
  errorMessage.value = '';
  try {
    const response = await getPendingEnrollments(discountTestDay.value);
    pendingEnrollments.value = response.data.enrollments || [];
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error del servidor de pagos';
  } finally {
    isLoadingEnrollments.value = false;
  }
}

async function loadPaymentHistory() {
  isLoadingHistory.value = true;
  errorMessage.value = '';
  try {
    const response = await getPaymentHistory();
    payments.value = response.data.payments || [];
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error del servidor de pagos';
  } finally {
    isLoadingHistory.value = false;
  }
}

async function loadCredits() {
  isLoadingCredits.value = true;
  errorMessage.value = '';
  try {
    const response = await getMyCredits();
    credits.value = response.data.credits || [];
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error cargando créditos';
  } finally {
    isLoadingCredits.value = false;
  }
}

async function loadNotifications() {
  isLoadingNotifications.value = true;
  errorMessage.value = '';
  try {
    const response = await getMyNotifications();
    notifications.value = response.data.notifications || [];
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error cargando notificaciones';
  } finally {
    isLoadingNotifications.value = false;
  }
}

async function loadDiscountRules() {
  if (!isDiscountTestVisible) return;

  try {
    const response = await getPaymentDiscountRules();
    discountRules.value = response.data || { periods: [] };
  } catch {
    discountRules.value = { periods: [] };
  }
}

async function payNow(enrollment) {
  errorMessage.value = '';
  isSubmittingId.value = enrollment.id;
  try {
    const response = await createPayment({
      enrollment_id: enrollment.id,
      payment_method: PAYMENT_METHOD.MERCADO_PAGO,
    });
    window.location.href = response.data.init_point;
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error del servidor de pagos';
    loadPendingEnrollments();
  } finally {
    isSubmittingId.value = null;
  }
}

onMounted(() => {
  loadDiscountRules();
  loadPendingEnrollments();
  loadPaymentHistory();
  loadCredits();
  loadNotifications();
});

watch(discountTestDay, () => {
  loadPendingEnrollments();
});

watch(
  () => route.query.tab,
  (tab) => {
    activeTab.value = PAYMENT_TABS.includes(tab) ? tab : PAYMENT_TAB.PENDING;
  }
);
</script>

<style scoped>
.payments-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 140px);
}

.payments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.payments-header h1 {
  color: #fff;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.payments-header p {
  color: #e0c0e0;
  font-size: 1.05rem;
  font-weight: 500;
}

.payments-header h1,
.history-section h2,
.enrollment-card h2,
.payment-summary h3 {
  margin: 0;
}

.payments-header p,
.eyebrow {
  margin: 0;
}

.payments-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.payments-tabs button.active {
  border-color: #f6ea98;
  background: #f6ea98;
  color: #9f5f91;
}

.return-message,
.history-section,
.discount-test-mode,
.error-message {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  color: #4a3a4a;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.enrollment-card {
  background: #fff;
  border: 2px solid #e8dce8;
  border-radius: 12px;
  color: #4a3a4a;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.return-message {
  font-weight: 700;
}

.return-message.success {
  border-color: #12b76a;
  color: #027a48 !important;
}

.return-message.pending {
  border-color: #f79009;
  color: #b54708 !important;
}

.return-message.failure,
.error-message {
  color: #b42318 !important;
}

.discount-test-mode {
  display: block;
  padding: 1.5rem 2rem 1.5rem;
}

.discount-test-mode legend {
  background: #fff;
  color: #572c57;
  font-weight: 700;
  line-height: 1.2;
  margin-left: 0.5rem;
  padding: 0 0.5rem;
}

.discount-test-mode label {
  align-items: center;
  cursor: pointer;
  display: inline-flex;
  gap: 8px;
  margin: 0.75rem 1.25rem 0 0;
}

.discount-test-mode input {
  margin: 0;
  width: auto;
}

.pending-section {
  display: grid;
  gap: 1rem;
}

.enrollment-card.highlighted {
  border-color: #9f5f91;
  box-shadow: 0 0 0 3px rgba(87, 44, 87, 0.14);
}

.enrollment-main {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  color: #9f5f91;
  font-family: "Poppins", sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 1px;
  line-height: 1.2;
  text-transform: uppercase;
}

.status-pill {
  background: #f6ea98;
  border-radius: 8px;
  color: #572c57;
  flex-shrink: 0;
  font-family: "Poppins", sans-serif;
  font-weight: 700;
  padding: 0.5rem 0.75rem;
}

.enrollment-details,
.payment-summary dl {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 1.25rem 0;
}

.payment-summary dl {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 0;
}

.enrollment-details div,
.payment-summary div {
  background: #f5e6f5;
  border: 1px solid #d0c0d0;
  border-radius: 10px;
  padding: 1rem;
}

dt {
  color: #572c57;
  font-family: "Poppins", sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

dd {
  color: #4a3a4a;
  font-weight: 700;
  margin: 0;
}

.pay-button {
  margin-top: 1rem;
}

.payments-table {
  border-collapse: collapse;
  color: #4a3a4a;
  width: 100%;
}

.payments-table th,
.payments-table td {
  border-bottom: 1px solid #e8dce8;
  padding: 10px;
  text-align: left;
}

.payments-table th {
  color: #572c57;
}

.notifications-list {
  display: grid;
  gap: 1rem;
}

.notification-item {
  align-items: flex-start;
  border: 1px solid #e8dce8;
  border-radius: 8px;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  padding: 1rem;
}

.notification-item h3,
.notification-item p {
  margin: 0;
}

.notification-item h3 {
  color: #572c57;
  font-size: 1rem;
}

.notification-item p {
  margin-top: 0.35rem;
}

.notification-item time {
  color: #8a6a8a;
  flex-shrink: 0;
  font-size: 0.9rem;
  font-weight: 700;
}

.empty-state {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  color: #8a6a8a;
  padding: 1.5rem;
  text-align: center;
}

@media (max-width: 760px) {
  .payments-header,
  .enrollment-main,
  .payments-tabs,
  .notification-item {
    display: block;
  }

  .payments-tabs button,
  .admin-link,
  .status-pill {
    display: inline-block;
    margin-top: 0.75rem;
  }

  .enrollment-details,
  .payment-summary dl {
    grid-template-columns: 1fr;
  }

  .payments-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
