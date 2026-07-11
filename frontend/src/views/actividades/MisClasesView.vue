<template>
  <main class="mis-clases-view">
    <header class="header">
      <div>
        <h1>Mis Clases</h1>
        <p>Visualizá turno a turno tus clases del mes. Podés darte de baja individualmente de la que no asistas.</p>
      </div>
      <router-link to="/" class="back-button">Volver al Inicio</router-link>
    </header>

    <p v-if="returnMessage" :class="['return-message', returnMessage.type]">
      {{ returnMessage.text }}
    </p>

    <section class="classes-list">
      <div class="filters">
        <button @click="filterType = 'mensuales'" :class="{ active: filterType === 'mensuales' }" class="filter-btn">Suscripciones Mensuales</button>
        <button @click="filterType = 'individuales'" :class="{ active: filterType === 'individuales' }" class="filter-btn">Clases Individuales</button>
        <button @click="filterType = 'lista-espera'" :class="{ active: filterType === 'lista-espera' }" class="filter-btn">Confirmación pendiente desde lista de espera</button>
      </div>

      <!-- Confirmación pendiente desde lista de espera -->
      <div v-if="filterType === 'lista-espera'" class="cards-grid waitlist-tab">
        <div v-if="isLoadingWaitlistInfo" class="empty-state" style="grid-column: 1 / -1;">Cargando tu lista de espera...</div>

        <template v-else-if="pendingWaitlistOffers.length > 0">
          <article v-for="offer in pendingWaitlistOffers" :key="offer.id" class="class-card offer-card">
            <div class="card-header">
              <h2>{{ offer.actividad }}</h2>
              <span class="status-pill pending">Confirmación pendiente</span>
            </div>
            <dl class="class-details">
              <div>
                <dt>Fecha y Hora</dt>
                <dd>{{ formatDateTime(offer.fecha_hora) }}</dd>
              </div>
              <div>
                <dt>Clase</dt>
                <dd>{{ offer.class_name }}</dd>
              </div>
            </dl>
            <p class="text-info small">Se liberó un cupo y fuiste seleccionado/a. Entrá para decidir si te inscribís o liberás el lugar.</p>
            <div class="card-actions">
              <router-link :to="`/lista-espera/oferta/${offer.id}`" class="cancel-button decide-button">Ver y decidir</router-link>
            </div>
          </article>
        </template>

        <div v-else-if="activeWaitlistEntries.length > 0" class="empty-state" style="grid-column: 1 / -1;">
          <p v-for="entry in activeWaitlistEntries" :key="entry.id">
            Aún no has sido seleccionado/a para la clase a la cual te has inscripto a la lista de espera de la clase
            <strong>{{ entry.actividad }} - {{ entry.class_name }}</strong> ({{ formatDateTime(entry.fecha_hora) }}).
          </p>
        </div>

        <div v-else class="empty-state" style="grid-column: 1 / -1;">
          No estás anotado/a en ninguna lista de espera actualmente.
        </div>
      </div>

      <div v-else-if="isLoading" class="empty-state">Cargando tus clases...</div>
      <div v-else-if="myClasses.length === 0" class="empty-state">No tenés turnos próximos registrados.</div>

      <!-- Clases Mensuales (Agrupadas) -->
      <div v-else-if="filterType === 'mensuales'" class="groups-container">
        <div v-if="monthlyGroups.length === 0" class="empty-state">No tenés suscripciones mensuales registradas.</div>
        <div v-for="group in monthlyGroups" :key="group.id" class="monthly-group">
          <div class="group-header" @click="toggleGroup(group.id)">
            <h2>{{ group.actividad }} - {{ group.dayName }} a las {{ group.time }} hs</h2>
            <span class="arrow">{{ openGroups[group.id] ? '▲' : '▼' }}</span>
          </div>
          <div v-if="openGroups[group.id]" class="group-content cards-grid">
            <article v-for="cls in group.clases" :key="cls.class_id" class="class-card" :class="{'is-cancelled': isCancelled(cls)}">
              <div class="card-header">
                <h2>{{ cls.actividad }}</h2>
                <span :class="['status-pill', statusClass(cls)]">{{ statusLabel(cls) }}</span>
              </div>
              
              <dl class="class-details">
                <div>
                  <dt>Fecha y Hora</dt>
                  <dd>{{ formatDateTime(cls.fecha_hora) }}</dd>
                </div>
                <div v-if="cls.room">
                  <dt>Salón</dt>
                  <dd>{{ cls.room }}</dd>
                </div>
                <div>
                  <dt>Tipo de Reserva</dt>
                  <dd>{{ cls.tipo }}</dd>
                </div>
              </dl>

              <div class="card-actions" v-if="!isCancelled(cls)">
                <button class="cancel-button" @click="confirmCancel(cls)" :disabled="isCancelling === cls.class_id">
                  {{ isCancelling === cls.class_id ? 'Cancelando...' : 'Dar de baja' }}
                </button>
              </div>
              <div class="card-actions" v-else-if="isClassCancelledByGym(cls)">
                <p class="text-danger small">El gimnasio canceló esta clase.</p>
              </div>
              <div class="card-actions" v-else>
                <p class="text-danger small">Te diste de baja de este turno.</p>
              </div>
            </article>
          </div>
        </div>
      </div>

      <!-- Clases Individuales (Sueltas) -->
      <div v-else-if="filterType === 'individuales'" class="cards-grid">
        <div v-if="individualClasses.length === 0" class="empty-state" style="grid-column: 1 / -1;">No tenés clases individuales registradas.</div>
        <article v-for="cls in individualClasses" :key="cls.class_id" class="class-card" :class="{'is-cancelled': isCancelled(cls)}">
          <div class="card-header">
            <h2>{{ cls.actividad }}</h2>
            <span :class="['status-pill', statusClass(cls)]">{{ statusLabel(cls) }}</span>
          </div>
          
          <dl class="class-details">
            <div>
              <dt>Fecha y Hora</dt>
              <dd>{{ formatDateTime(cls.fecha_hora) }}</dd>
            </div>
            <div v-if="cls.room">
              <dt>Salón</dt>
              <dd>{{ cls.room }}</dd>
            </div>
            <div>
              <dt>Tipo de Reserva</dt>
              <dd>{{ cls.tipo }}</dd>
            </div>
          </dl>

          <div class="card-actions" v-if="!isCancelled(cls)">
            <button class="cancel-button" @click="confirmCancel(cls)" :disabled="isCancelling === cls.class_id">
              {{ isCancelling === cls.class_id ? 'Cancelando...' : 'Dar de baja' }}
            </button>
          </div>
          <div class="card-actions" v-else-if="isClassCancelledByGym(cls)">
            <p class="text-danger small">El gimnasio canceló esta clase.</p>
          </div>
          <div class="card-actions" v-else>
            <p class="text-danger small">Te diste de baja de este turno.</p>
          </div>
        </article>
      </div>
    </section>

    <!-- Modal de confirmación: baja de un día -->
    <div v-if="selectedClass" class="modal-backdrop" @click.self="selectedClass = null">
      <div class="modal">
        <h2>Confirmar Baja</h2>
        <p>¿Seguro querés cancelar tu asistencia a la clase de <strong>{{ selectedClass.actividad }}</strong> del <strong>{{ formatDateTime(selectedClass.fecha_hora) }}</strong>?</p>
        <p class="warning">
          Se generará un <strong>crédito para anotarte a una clase individual</strong> de la misma actividad y liberarás el cupo para alguien más.
        </p>
        <div class="modal-actions">
          <button class="secondary-button" @click="selectedClass = null">Cerrar</button>
          <button class="danger-button" @click="submitCancel">Confirmar Baja</button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { getPendingEnrollments, getMyWaitlists } from '../../services/api';
import { formatDateTime } from '../../utils/formatters';
import { CLASS_STATUS, ENROLLMENT_STATUS } from '../../constants/statuses';

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
const route = useRoute();

const myClasses = ref([]);
const isLoading = ref(false);
const isCancelling = ref(null);
const selectedClass = ref(null);

const filterType = ref('mensuales');
const openGroups = ref({});

const isLoadingWaitlistInfo = ref(false);
const pendingWaitlistOffers = ref([]);
const activeWaitlistEntries = ref([]);

const returnMessage = computed(() => {
  const status = route.query.status;
  if (status === 'success') {
    return { type: 'success', text: 'Inscripción exitosa' };
  }
  return null;
});

function toggleGroup(groupId) {
  openGroups.value[groupId] = !openGroups.value[groupId];
}

const individualClasses = computed(() => {
  return myClasses.value.filter(c => c.tipo !== 'Mensual');
});

const monthlyGroups = computed(() => {
  const groups = {};
  myClasses.value.filter(c => c.tipo === 'Mensual').forEach(cls => {
    if (!cls.fecha_hora) return;
    const dateObj = new Date(cls.fecha_hora);
    const days = ['Domingos', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábados'];
    const dayName = days[dateObj.getDay()];
    
    let time = '';
    if (cls.fecha_hora.includes('T')) {
      time = cls.fecha_hora.split('T')[1].substring(0, 5);
    } else {
      time = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    const key = `${cls.actividad}-${dayName}-${time}`;

    if (!groups[key]) {
      groups[key] = { id: key, actividad: cls.actividad, dayName, time, clases: [] };
    }
    groups[key].clases.push(cls);
  });
  return Object.values(groups).sort((a, b) => a.id.localeCompare(b.id));
});

function isCancelled(cls) {
  const isEnrCancelled = String(cls.estado_inscripcion).toLowerCase() === 'cancelada' || String(cls.estado_inscripcion).toLowerCase() === 'cancelled';
  const isClsCancelled = String(cls.estado_clase).toLowerCase() === 'cancelada' || String(cls.estado_clase).toLowerCase() === 'cancelled';
  return isEnrCancelled || isClsCancelled || cls.estado_inscripcion === ENROLLMENT_STATUS.CANCELLED || cls.estado_clase === CLASS_STATUS.CANCELLED;
}

function isClassCancelledByGym(cls) {
  const isClsCancelled = String(cls.estado_clase).toLowerCase() === 'cancelada' || String(cls.estado_clase).toLowerCase() === 'cancelled';
  return isClsCancelled || cls.estado_clase === CLASS_STATUS.CANCELLED;
}

function statusClass(cls) {
  if (isCancelled(cls)) return 'cancelled';
  if (cls.estado_inscripcion === ENROLLMENT_STATUS.PAID) return 'paid';
  return 'pending';
}

function statusLabel(cls) {
  if (isCancelled(cls)) return 'Cancelada';
  if (cls.estado_inscripcion === ENROLLMENT_STATUS.PAID) return 'Confirmada';
  return 'Pendiente';
}

async function loadClasses() {
  isLoading.value = true;
  try {
    const response = await axios.get(`${baseURL}/classes/my`, { withCredentials: true });
    myClasses.value = response.data.classes || [];
  } catch (err) {
    console.error("Error cargando mis clases:", err);
  } finally {
    isLoading.value = false;
  }
}

async function loadWaitlistInfo() {
  isLoadingWaitlistInfo.value = true;
  try {
    const [pendingResponse, waitlistResponse] = await Promise.all([
      getPendingEnrollments(),
      getMyWaitlists(),
    ]);
    pendingWaitlistOffers.value = (pendingResponse.data.enrollments || []).filter((e) => e.waitlist_offer);
    activeWaitlistEntries.value = waitlistResponse.data.waitlists || [];
  } catch (err) {
    console.error("Error cargando la lista de espera:", err);
  } finally {
    isLoadingWaitlistInfo.value = false;
  }
}

function confirmCancel(cls) { selectedClass.value = cls; }

async function submitCancel() {
  if (!selectedClass.value) return;
  const cls = selectedClass.value;
  isCancelling.value = cls.class_id;
  selectedClass.value = null;
  try {
    const response = await axios.post(`${baseURL}/classes/${cls.class_id}/cancel-attendance`, {}, { withCredentials: true });
    alert(response.data.message);
    loadClasses();
  } catch (err) {
    alert(err.response?.data?.error || 'Error al cancelar la clase.');
  } finally {
    isCancelling.value = null;
  }
}

onMounted(() => { loadClasses(); loadWaitlistInfo(); });
</script>

<style scoped>
.mis-clases-view { padding: 24px; max-width: 1000px; margin: 0 auto; min-height: calc(100vh - 140px); }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; gap: 1rem;}
.header h1 { color: #fff; margin: 0 0 0.5rem 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
.header p { color: #e0c0e0; margin: 0; font-size: 1.05rem; }
.back-button { background: #f6ea98; padding: 10px 16px; border-radius: 8px; color: #572c57; text-decoration: none; font-weight: 700; white-space: nowrap;}
.empty-state { background: #fff; padding: 2rem; text-align: center; border-radius: 12px; color: #8a6a8a; border: 2px solid #d0c0d0; }
.return-message { margin-bottom: 1.5rem; padding: 1rem; border-radius: 10px; border-left: 4px solid transparent; font-weight: 700; }
.return-message.success { color: #027a48; background: #ecfdf3; border-left-color: #12b76a; }
.return-message.error { color: #b91c1c; background: #fee2e2; border-left-color: #b91c1c; }

.filters { display: flex; gap: 1rem; margin-bottom: 2rem; }
.filter-btn { background: transparent; border: 2px solid #f0e6f0; border-radius: 8px; color: #8a6a8a; font-size: 1.05rem; font-weight: 700; padding: 0.75rem 1.5rem; cursor: pointer; transition: 0.2s; }
.filter-btn.active { background: #f5e6f5; border-color: #d0c0d0; color: #572c57; }
.filter-btn:hover:not(.active) { border-color: #d0c0d0; color: #572c57; }

.groups-container { display: flex; flex-direction: column; gap: 1.5rem; }
.monthly-group { background: #fff; border: 2px solid #e8dce8; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }
.group-header { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 1.5rem; background: #f5e6f5; cursor: pointer; user-select: none; transition: background 0.2s; }
.group-header:hover { background: #ede5f5; }
.group-header h2 { margin: 0; color: #572c57; font-size: 1.2rem; }
.group-content { padding: 1.5rem; border-top: 2px solid #e8dce8; background: #fafafa; }
.arrow { color: #9f5f91; font-size: 0.9rem; font-weight: 700; }

.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
.class-card { background: #fff; border: 2px solid #e8dce8; border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; box-shadow: 0 8px 30px rgba(0,0,0,0.05); }
.class-card.is-cancelled { opacity: 0.6; background: #fafafa; border-style: dashed; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.card-header h2 { margin: 0; color: #572c57; font-size: 1.25rem; }
.status-pill { padding: 4px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; }
.status-pill.paid { background: #eef8f1; color: #027a48; }
.status-pill.pending { background: #fef0c7; color: #b54708; }
.status-pill.cancelled { background: #fee2e2; color: #b42318; }
.class-details { display: grid; gap: 1rem; margin-bottom: 1.5rem; flex: 1; }
.class-details div { background: #f9f9f9; padding: 0.75rem; border-radius: 8px; border: 1px solid #e8dce8; }
dt { font-size: 0.85rem; color: #8a6a8a; font-weight: 600; margin-bottom: 4px; }
dd { margin: 0; font-weight: 700; color: #4a3a4a; }
.cancel-button { width: 100%; background: #fee2e2; color: #b42318; border: 1px solid #fca5a5; padding: 0.75rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
.cancel-button:hover:not(:disabled) { background: #fecaca; }
.text-danger { color: #b42318; margin: 0; text-align: center; font-weight: 600; }
.text-info { color: #572c57; margin: 0 0 1rem 0; }
.small { font-size: 0.85rem; }
.decide-button { display: inline-block; text-align: center; text-decoration: none; }
.waitlist-tab .empty-state p { margin: 0 0 0.75rem 0; }
.waitlist-tab .empty-state p:last-child { margin-bottom: 0; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; padding: 1rem;}
.modal { background: #fff; padding: 2rem; border-radius: 12px; max-width: 450px; width: 100%; }
.modal h2 { margin-top: 0; color: #572c57; }
.warning { font-size: 0.9rem; color: #b54708; background: #fef0c7; padding: 1rem; border-radius: 8px; margin: 1rem 0; line-height: 1.4; border: 1px solid #fbd28e;}
.modal-actions { display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem; }
.secondary-button { background: #f1f1f1; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; font-weight: 600; color: #4a3a4a;}
.danger-button { background: #b42318; color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; font-weight: 600; }
</style>
