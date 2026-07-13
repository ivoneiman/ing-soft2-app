<template>
  <main class="payments-view">
    <header class="payments-header">
      <div>
        <h1>Pagos</h1>
        <p>Historial de pagos y créditos.</p>
      </div>

      <RouterLink v-if="isAdmin" to="/admin/descuentos" class="admin-link">
        Configurar descuentos
      </RouterLink>
    </header>

    <p v-if="returnMessage" :class="['return-message', returnMessage.type]">
      {{ returnMessage.text }}
    </p>

    <section v-if="activeTab === PAYMENT_TAB.HISTORY" class="history-section">
      <h2>Historial de pagos</h2>

      <div v-if="isLoadingHistory" class="empty-state">Cargando pagos...</div>
      <div v-else-if="payments.length === 0" class="empty-state">Todavía no hay pagos registrados.</div>

      <table v-else class="payments-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Actividad</th>
            <th>Monto Pagado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in payments" :key="payment.id">
            <td>{{ formatDateOnly(payment.created_at) }}</td>
            <td>{{ formatTime(payment.created_at) }}</td>
            <td>{{ payment.actividad || payment.class_name || '-' }}</td>
            <td>{{ formatMoney(payment.final_amount) }}</td>
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
            <th>Tipo</th>
            <th>Vencimiento</th>
            <th>Origen</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="credit in credits" :key="credit.id">
            <td>{{ credit.actividad_name || '-' }}</td>
            <td>{{ creditTypeLabel(credit.tipo) }}</td>
            <td>{{ formatDateTime(credit.expires_at || credit.fecha_expiracion) }}</td>
            <td>{{ credit.origin_class_name || '-' }}</td>
            <td>{{ creditStatusLabel(credit.status) }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { ENROLLMENT_TYPE, statusLabel } from '../../constants/statuses';
import { PAYMENT_RETURN_MESSAGES, PAYMENT_RETURN_STATUS, PAYMENT_TAB, PAYMENT_TABS } from '../../constants/payments';
import {
  getMyCredits,
  getPaymentHistory,
} from '../../services/api';
import { formatDateOnly, formatDateTime, formatMoney, formatTime } from '../../utils/formatters';
import { roleHelpers } from '../../utils/roleHelpers';

const route = useRoute();
const isAdmin = ref(roleHelpers.isAdmin());
function normalizedTab(tab) {
  return PAYMENT_TABS.includes(tab) ? tab : PAYMENT_TAB.HISTORY;
}

const activeTab = ref(normalizedTab(route.query.tab));
const isLoadingHistory = ref(false);
const isLoadingCredits = ref(false);
const payments = ref([]);
const credits = ref([]);

const returnMessage = computed(() => {
  if (PAYMENT_RETURN_MESSAGES[route.query.status]) return PAYMENT_RETURN_MESSAGES[route.query.status];
  if (route.query.status === PAYMENT_RETURN_STATUS.FAILURE) return { type: 'failure', text: route.query.message || 'Pago rechazado' };
  return null;
});

function creditStatusLabel(status) {
  return statusLabel('credit', status);
}

function creditTypeLabel(tipo) {
  if (tipo === ENROLLMENT_TYPE.MONTHLY) return 'Mensual';
  return 'Individual';
}

async function loadPaymentHistory() {
  isLoadingHistory.value = true;
  try {
    const response = await getPaymentHistory();
    payments.value = response.data.payments || [];
  } catch (err) {
    console.error("Error cargando el historial de pagos:", err);
  } finally {
    isLoadingHistory.value = false;
  }
}

async function loadCredits() {
  isLoadingCredits.value = true;
  try {
    const response = await getMyCredits();
    credits.value = response.data.credits || [];
  } catch (err) {
    console.error("Error cargando créditos:", err);
  } finally {
    isLoadingCredits.value = false;
  }
}

onMounted(() => {
  loadPaymentHistory();
  loadCredits();
});

watch(
  () => route.query.tab,
  (tab) => {
    activeTab.value = normalizedTab(tab);
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
.history-section h2 {
  margin: 0;
}

.payments-header p {
  margin: 0;
}

.return-message,
.history-section,
.discount-test-mode {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  color: #4a3a4a;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
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

.return-message.failure {
  color: #b42318 !important;
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

.empty-state {
  background: #fff;
  border: 2px solid #d0c0d0;
  border-radius: 20px;
  color: #8a6a8a;
  padding: 1.5rem;
  text-align: center;
}

@media (max-width: 760px) {
  .payments-header {
    display: block;
  }

  .payments-view {
    padding: 16px;
  }

  .admin-link {
    display: inline-block;
    margin-top: 0.75rem;
  }

  .payments-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
