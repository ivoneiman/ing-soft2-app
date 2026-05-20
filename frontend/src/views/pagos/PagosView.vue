<template>
  <main class="payments-view">
    <header class="payments-header">
      <div>
        <h1>Pagos</h1>
        <p>Suscripciones, clases individuales e historial.</p>
      </div>

      <RouterLink v-if="isAdmin" to="/admin/descuentos" class="admin-link">
        Configurar descuentos
      </RouterLink>
    </header>

    <p v-if="returnMessage" :class="['return-message', returnMessage.type]">
      {{ returnMessage.text }}
    </p>

    <section class="payment-panel">
      <form class="payment-form" @submit.prevent="handleSubmit">
        <div class="field">
          <label for="class-id">Actividad / clase</label>
          <select id="class-id" v-model="form.class_id" required>
            <option value="" disabled>Seleccionar actividad</option>
            <option v-for="classItem in payableClasses" :key="classItem.id" :value="classItem.id">
              {{ classItem.actividad }} - {{ formatDate(classItem.fecha_hora) }}
            </option>
          </select>
          <span v-if="payableClasses.length === 0" class="field-help">
            No hay clases futuras disponibles para pagar.
          </span>
        </div>

        <div class="field">
          <label for="payment-type">Tipo de pago</label>
          <select id="payment-type" v-model="form.payment_type" required>
            <option value="" disabled>Seleccionar tipo de pago</option>
            <option value="monthly_subscription">Suscripción mensual</option>
            <option value="individual_class">Clase individual</option>
          </select>
        </div>

        <div class="field">
          <label for="payment-option">Forma</label>
          <select id="payment-option" v-model="form.payment_option" required>
            <option value="" disabled>Seleccionar forma de pago</option>
            <option value="full">Pago completo</option>
            <option value="deposit">Seña</option>
          </select>
        </div>

        <fieldset v-if="isDiscountTestVisible" class="discount-test-mode">
          <legend>Modo testing descuentos</legend>
          <label v-for="option in discountTestOptions" :key="option.value">
            <input v-model="discountTestDay" type="radio" name="discount-test-day" :value="option.value" />
            <span>{{ option.label }}</span>
          </label>
        </fieldset>

        <section v-if="isPaymentReady" class="payment-summary">
          <h2>Resumen</h2>
          <dl>
            <div>
              <dt>Clase</dt>
              <dd>{{ selectedClass.actividad }}</dd>
            </div>
            <div>
              <dt>Precio original</dt>
              <dd>{{ formatMoney(summary.amount) }}</dd>
            </div>
            <div>
              <dt>Descuento aplicado</dt>
              <dd>{{ summary.discountPercentage }}%</dd>
            </div>
            <div>
              <dt>Monto final</dt>
              <dd>{{ formatMoney(summary.finalAmount) }}</dd>
            </div>
          </dl>
        </section>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

        <button class="pay-button" type="submit" :disabled="isSubmitting || !isPaymentReady">
          {{ isSubmitting ? 'Redirigiendo...' : 'Realizar pago' }}
        </button>
      </form>
    </section>

    <section class="history-section">
      <h2>Historial</h2>

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
            <td>{{ formatDate(payment.created_at) }}</td>
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
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { createPayment, getPaymentClasses, getPaymentHistory } from '../../services/api';
import { roleHelpers } from '../../utils/roleHelpers';

const route = useRoute();
const isAdmin = ref(roleHelpers.isAdmin());
const isSubmitting = ref(false);
const isLoadingHistory = ref(false);
const errorMessage = ref('');
const classes = ref([]);
const payments = ref([]);
const discountTestDay = ref('');
const isDiscountTestVisible = import.meta.env.DEV || import.meta.env.MODE === 'test';
const discountTestOptions = [
  { value: '', label: 'Fecha real' },
  { value: '10', label: 'Simular día 10 (0%)' },
  { value: '17', label: 'Simular día 17 (40%)' },
  { value: '25', label: 'Simular día 25 (70%)' },
];

const form = reactive({
  class_id: '',
  payment_type: '',
  payment_method: 'mercado_pago',
  payment_option: '',
});

const payableClasses = computed(() => {
  return classes.value.filter((classItem) => classItem.is_payable !== false);
});

const selectedClass = computed(() => {
  return payableClasses.value.find((classItem) => String(classItem.id) === String(form.class_id));
});

const isPaymentReady = computed(() => {
  return Boolean(
    selectedClass.value &&
    form.payment_type &&
    form.payment_option
  );
});

const summary = computed(() => {
  if (!isPaymentReady.value) {
    return {
      amount: 0,
      discountPercentage: 0,
      finalAmount: 0,
    };
  }

  const quote = selectedClass.value.quotes?.[form.payment_type]?.[form.payment_option];

  return {
    amount: Number(quote?.amount || 0),
    discountPercentage: Number(quote?.discount_percentage || 0),
    finalAmount: Number(quote?.final_amount || 0),
  };
});

const returnMessage = computed(() => {
  if (route.query.status === 'success') {
    return { type: 'success', text: 'Pago aprobado' };
  }

  if (route.query.status === 'pending') {
    return { type: 'pending', text: 'Pago pendiente' };
  }

  if (route.query.status === 'failure') {
    return { type: 'failure', text: route.query.message || 'Pago rechazado' };
  }

  return null;
});

function formatDate(value) {
  if (!value) {
    return '-';
  }

  return new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatMoney(value) {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(Number(value || 0));
}

function paymentMethodLabel(paymentMethod) {
  return paymentMethod === 'mercado_pago' ? 'Mercado Pago' : '-';
}

function paymentStatusLabel(status) {
  const labels = {
    approved: 'Aprobado',
    rejected: 'Rechazado',
    pending: 'Pendiente',
  };

  return labels[status] || status;
}

async function loadClasses() {
  try {
    const response = await getPaymentClasses(discountTestDay.value);
    classes.value = response.data.classes || [];
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error del servidor de pagos';
  }
}

async function loadPaymentHistory() {
  isLoadingHistory.value = true;
  try {
    const response = await getPaymentHistory();
    payments.value = response.data.payments || [];
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error del servidor de pagos';
  } finally {
    isLoadingHistory.value = false;
  }
}

async function handleSubmit() {
  errorMessage.value = '';

  if (!isPaymentReady.value) {
    errorMessage.value = 'Debe completar todos los campos para realizar el pago';
    return;
  }

  isSubmitting.value = true;

  try {
    const response = await createPayment({
      class_id: form.class_id,
      payment_type: form.payment_type,
      payment_method: form.payment_method,
      payment_option: form.payment_option,
    });

    window.location.href = response.data.init_point;
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Error del servidor de pagos';
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(() => {
  loadClasses();
  loadPaymentHistory();
});

watch(discountTestDay, () => {
  loadClasses();
});
</script>

<style scoped>
.payments-view {
  width: min(1040px, calc(100% - 32px));
  margin: 0 auto;
  padding: 32px 0;
}

.payments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.payments-header h1 {
  margin: 0 0 6px;
  font-size: 32px;
}

.payments-header p {
  margin: 0;
}

.admin-link,
.pay-button {
  border: 0;
  border-radius: 6px;
  background: #572c57;
  color: #fff;
  cursor: pointer;
  font-weight: 700;
  padding: 12px 16px;
  text-decoration: none;
}

.return-message,
.payment-panel,
.history-section {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.return-message {
  font-weight: 700;
}

.return-message.success {
  border-color: #12b76a;
  color: #027a48;
}

.return-message.pending {
  border-color: #f79009;
  color: #b54708;
}

.return-message.failure,
.error-message {
  color: #b42318;
}

.payment-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  font-weight: 700;
}

.field select {
  border: 1px solid #bbb;
  border-radius: 6px;
  min-height: 42px;
  padding: 8px 10px;
}

.discount-test-mode {
  grid-column: 1 / -1;
  border: 1px solid #ddd;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  margin: 0;
  padding: 14px 16px 16px;
}

.discount-test-mode legend {
  font-weight: 700;
  padding: 0 6px;
}

.discount-test-mode label {
  align-items: center;
  cursor: pointer;
  display: inline-flex;
  gap: 8px;
}

.field-help {
  color: #666;
  font-size: 14px;
}

.payment-summary,
.error-message,
.pay-button {
  grid-column: 1 / -1;
}

.payment-summary {
  border-top: 1px solid #ddd;
  padding-top: 16px;
}

.payment-summary h2 {
  font-size: 20px;
  margin: 0 0 12px;
}

.payment-summary dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
}

.payment-summary div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.payment-summary dt {
  font-weight: 700;
}

.payment-summary dd {
  margin: 0;
}

.error-message {
  margin: 0;
}

.pay-button {
  justify-self: start;
}

.pay-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.history-section h2 {
  margin: 0 0 16px;
}

.payments-table {
  border-collapse: collapse;
  width: 100%;
}

.payments-table th,
.payments-table td {
  border-bottom: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

.empty-state {
  padding: 16px 0;
}

@media (max-width: 700px) {
  .payments-header,
  .payment-form,
  .payment-summary dl {
    display: block;
  }

  .admin-link,
  .field,
  .pay-button,
  .payment-summary div {
    margin-top: 14px;
  }

  .payments-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
