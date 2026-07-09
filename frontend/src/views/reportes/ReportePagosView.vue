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
      <div class="search-container">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Buscar cliente por nombre o apellido..." 
          class="search-input"
        />
      </div>
      <div class="filters-header">
        <h3>Filtros</h3>
      </div>
      <div class="filters-container">
        <div class="date-filter-group">
          <label for="start-date">Fecha Desde</label>
          <input type="date" id="start-date" v-model="filterStartDate" class="filter-input" title="Fecha desde" />
        </div>
        <div class="date-filter-group">
          <label for="end-date">Fecha Hasta</label>
          <input type="date" id="end-date" v-model="filterEndDate" class="filter-input" title="Fecha hasta" :disabled="!filterStartDate" />
        </div>
      </div>
      <div class="filters-container">
        <select v-model="filterActivity" class="filter-input" title="Filtrar por actividad">
          <option value="">Todas las actividades</option>
          <option v-for="act in availableActivities" :key="act" :value="act">
            {{ act }}
          </option>
        </select>
        <select v-model="filterYear" class="filter-input" title="Filtrar por año">
          <option value="">Todos los años</option>
          <option v-for="year in generatedYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
        <select v-model="filterMonth" class="filter-input" title="Filtrar por mes">
          <option value="">Todos los meses</option>
          <option v-for="month in staticMonths" :key="month.value" :value="month.value">
            {{ month.label }}
          </option>
        </select>
        <select v-model="filterDay" class="filter-input" title="Filtrar por día">
          <option value="">Todos los días</option>
          <option v-for="day in daysInSelectedMonth" :key="day" :value="day">
            {{ day }}
          </option>
        </select>
      </div>

      <div v-if="isLoading" class="empty-state mt-4">Cargando pagos...</div>
      <div v-else-if="filteredPayments.length === 0" class="empty-state mt-4">No se encontraron pagos con esos filtros.</div>

      <table v-else class="users-table mt-4">
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
          <tr v-for="pay in filteredPayments" :key="pay.id" :class="{'is-debt': pay.status === 'pending_payment' && !isCancelled(pay), 'is-cancelled': isCancelled(pay)}">
            <td>{{ formatDateTime(pay.created_at) }}</td>
            <td class="bold">{{ pay.user?.apellido }} {{ pay.user?.username }}</td>
            <td>{{ pay.actividad || '-' }}</td>
            <td>{{ paymentMethodLabel(pay.payment_method) }}</td>
            <td>{{ paymentTypeLabel(pay.payment_type) }}</td>
            <td class="bold money">
              <span v-if="isCancelled(pay)">-</span>
              <span v-else>{{ formatMoney(pay.final_amount) }}</span>
            </td>
            <td>
              <template v-if="isCancelled(pay)">
                <span v-if="pay.requiere_reembolso" class="status-pill expired">Cancelada (Reembolso pdte.)</span>
                <span v-else-if="pay.payment_method !== '-'" class="status-pill expired">Cancelada (Créditos)</span>
                <span v-else class="status-pill expired">Cancelada</span>
              </template>
              <template v-else>
                <span :class="['status-pill', pay.status]">{{ paymentStatusLabel(pay.status) }}</span>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { formatDateTime, formatMoney } from '../../utils/formatters';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const payments = ref([]);
const isLoading = ref(false);
const searchQuery = ref('');
const filterActivity = ref('');
const filterYear = ref('');
const filterMonth = ref('');
const filterDay = ref('');
const filterStartDate = ref('');
const filterEndDate = ref('');

const availableActivities = computed(() => {
  const acts = new Set();
  payments.value.forEach(p => {
    if (p.actividad && p.actividad !== '-') acts.add(p.actividad);
  });
  return Array.from(acts).sort();
});

const generatedYears = computed(() => {
  const currentYear = new Date().getFullYear();
  return [currentYear - 1, currentYear, currentYear + 1].map(String);
});

const staticMonths = [
  { value: '01', label: 'Enero' },
  { value: '02', label: 'Febrero' },
  { value: '03', label: 'Marzo' },
  { value: '04', label: 'Abril' },
  { value: '05', label: 'Mayo' },
  { value: '06', label: 'Junio' },
  { value: '07', label: 'Julio' },
  { value: '08', label: 'Agosto' },
  { value: '09', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' }
];

const daysInSelectedMonth = computed(() => {
  if (!filterYear.value || !filterMonth.value) return 31;
  return new Date(parseInt(filterYear.value), parseInt(filterMonth.value), 0).getDate();
});

const filteredPayments = computed(() => {
  return payments.value.filter(pay => {
    let matchQuery = true;
    let matchActivity = true;
    let matchYear = true;
    let matchMonth = true;
    let matchDay = true;
    let matchDateRange = true;

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase().trim();
      const user = pay.user || {};
      const fullName = `${user.username || ''} ${user.apellido || ''}`.toLowerCase();
      const reversedName = `${user.apellido || ''} ${user.username || ''}`.toLowerCase();
      
      matchQuery = fullName.includes(query) || reversedName.includes(query);
    }

    if (filterActivity.value) {
      matchActivity = pay.actividad === filterActivity.value;
    }

    if (filterYear.value) {
      if (pay.created_at) {
        matchYear = pay.created_at.startsWith(filterYear.value);
      } else {
        matchYear = false;
      }
    }

    if (filterMonth.value) {
      if (pay.created_at) {
        const monthStr = pay.created_at.split('-')[1];
        matchMonth = monthStr === filterMonth.value;
      } else {
        matchMonth = false;
      }
    }

    if (filterDay.value) {
      if (pay.created_at) {
        const dayStr = pay.created_at.split('T')[0].split('-')[2];
        matchDay = parseInt(dayStr, 10) === parseInt(filterDay.value, 10);
      } else {
        matchDay = false;
      }
    }

    if (filterStartDate.value && filterEndDate.value) {
      if (pay.created_at) {
        const paymentDate = pay.created_at.split('T')[0];
        matchDateRange = paymentDate >= filterStartDate.value && paymentDate <= filterEndDate.value;
      } else {
        matchDateRange = false;
      }
    }
    return matchQuery && matchActivity && matchYear && matchMonth && matchDay && matchDateRange;
  });
});

function isCancelled(pay) {
  const estadoInsc = String(pay.estado_inscripcion || '').toLowerCase();
  const estadoClas = String(pay.estado_clase || '').toLowerCase();
  return ['cancelada', 'cancelled'].includes(estadoInsc) || ['cancelada', 'cancelled'].includes(estadoClas);
}

function paymentMethodLabel(method) {
  if (method === '-') return '-';
  const labels = { cash: 'Efectivo', mercado_pago: 'Mercado Pago' };
  return labels[method] || method;
}

function paymentTypeLabel(type) {
  const labels = { full: 'Cobro Total', deposit: 'Seña', pending_enrollment: 'Deuda (Inscripción)' };
  return labels[type] || type;
}

function paymentStatusLabel(status) {
  const labels = { approved: 'Cobrado', pending: 'Pendiente', rejected: 'Rechazado', pending_payment: 'Falta Pagar' };
  return labels[status] || status;
}

async function loadPayments() {
  isLoading.value = true;
  try {
    const response = await axios.get(`${baseURL}/admin/enrollments/payments`, { withCredentials: true });
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

.search-container {
  margin-bottom: 1rem;
}
.search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 16px;
  border: 1px solid #d0c0d0;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  color: #4a3a4a;
  transition: border-color 0.2s;
}

.filters-header {
  margin-bottom: 0.5rem;
}
.filters-header h3 {
  color: #572c57;
  margin: 0;
  font-size: 1.1rem;
}

.filters-container {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.date-filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}
.date-filter-group label {
  font-size: 0.8rem; color: #572c57; margin-left: 4px;
}
.filter-input {
  flex: 1;
  min-width: 160px;
  padding: 12px 16px;
  border: 1px solid #d0c0d0;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  color: #4a3a4a;
  background-color: #fff;
  transition: border-color 0.2s;
}
.search-input:focus, .filter-input:focus {
  border-color: #9f5f91;
}
.mt-4 {
  margin-top: 1.5rem;
}

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
.is-cancelled td {
  opacity: 0.6;
  background-color: #fafafa;
}
</style>