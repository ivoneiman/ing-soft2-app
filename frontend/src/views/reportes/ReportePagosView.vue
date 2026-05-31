<template>
  <main class="report-view">
    <header class="report-header">
      <div>
        <h1>Historial de Pagos</h1>
        <p>Registro global de transacciones, señas y estados de pago.</p>
      </div>
      <router-link to="/reportes" class="back-button">
        Volver a Reportes
      </router-link>
    </header>

    <section class="table-section">
      <div v-if="isLoading" class="empty-state">Cargando pagos...</div>
      <div v-else-if="payments.length === 0" class="empty-state">No hay pagos registrados aún.</div>

      <table v-else class="users-table">
        <thead>
          <tr>
            <th>Fecha y Hora</th>
            <th>Cliente</th>
            <th>Actividad</th>
            <th>Método</th>
            <th>Tipo de Pago</th>
            <th>Monto</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pay in payments" :key="pay.id" :class="{'is-debt': pay.status === 'pending_payment'}">
            <td>{{ formatDateTime(pay.created_at) }}</td>
            <td class="bold">{{ pay.user?.apellido }} {{ pay.user?.username }}</td>
            <td>{{ pay.actividad || '-' }}</td>
            <td>{{ paymentMethodLabel(pay.payment_method) }}</td>
            <td>{{ paymentTypeLabel(pay.payment_type) }}</td>
            <td class="bold money">{{ formatMoney(pay.final_amount) }}</td>
            <td><span :class="['status-pill', pay.status]">{{ paymentStatusLabel(pay.status) }}</span></td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { formatDateTime, formatMoney } from '../../utils/formatters';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const payments = ref([]);
const isLoading = ref(false);

function paymentMethodLabel(method) {
  if (method === '-') return '-';
  const labels = { cash: 'Efectivo', transfer: 'Transferencia', card: 'Tarjeta', mercado_pago: 'Mercado Pago' };
  return labels[method] || method;
}

function paymentTypeLabel(type) {
  const labels = { full: 'Cobro Total', deposit: 'Seña', balance: 'Saldo', pending_enrollment: 'Deuda (Inscripción)' };
  return labels[type] || type;
}

function paymentStatusLabel(status) {
  const labels = { approved: 'Cobrado', pending: 'Pendiente', rejected: 'Rechazado', pending_payment: 'Falta Pagar' };
  return labels[status] || status;
}

async function loadPayments() {
  isLoading.value = true;
  try {
    const response = await axios.get(`${baseURL}/admin/reportes/pagos`, { withCredentials: true });
    payments.value = response.data.payments || [];
  } catch (err) {
    console.error("Error cargando el historial global de pagos:", err);
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  loadPayments();
});
</script>

<style scoped>
.report-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 140px);
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.report-header h1 { color: #fff; margin: 0 0 0.5rem 0; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3); }
.report-header p { color: #e0c0e0; font-size: 1.05rem; margin: 0; }

.back-button {
  background: #f6ea98; border: none; border-radius: 8px; color: #572c57;
  font-weight: 700; padding: 10px 16px; text-decoration: none;
}

.table-section, .empty-state {
  background: #fff; border: 2px solid #d0c0d0; border-radius: 20px;
  padding: 2rem; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2); overflow-x: auto;
}
.empty-state { text-align: center; color: #8a6a8a; }

.users-table { width: 100%; border-collapse: collapse; color: #4a3a4a; min-width: 800px;}
.users-table th, .users-table td { padding: 12px; border-bottom: 1px solid #e8dce8; text-align: left; }
.users-table th { color: #572c57; }
.bold { font-weight: 700; }
.money { color: #027a48; }

.status-pill {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}
.status-pill.approved {
  background: #eef8f1;
  color: #027a48;
}
.status-pill.pending,
.status-pill.pending_payment {
  background: #fef0c7;
  color: #b54708;
}
.status-pill.rejected {
  background: #fee2e2;
  color: #b42318;
}
.status-pill.expired {
  background: #f3f4f6;
  color: #4b5563;
}

/* Resaltar visualmente las filas de deuda */
.is-debt td {
  background-color: #fff9f9;
}
.is-debt .status-pill.pending_payment {
  background: #fee2e2;
  color: #b42318;
}
</style>