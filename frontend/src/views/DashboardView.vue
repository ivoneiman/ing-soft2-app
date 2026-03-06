<template>
  <div style="max-width: 700px; margin: 40px auto; padding: 0 16px;">
    <h1 style="margin-bottom: 24px;">Dashboard</h1>

    <!-- Formulario nueva nota -->
    <div class="card" style="max-width: 100%; margin: 0 0 24px 0;">
      <h3 style="margin-bottom: 12px;">Nueva nota</h3>
      <input v-model="newTitle" type="text" placeholder="Título" />
      <textarea
        v-model="newContent"
        placeholder="Contenido (opcional)"
        style="width:100%; padding:10px; border:1px solid #ddd; border-radius:6px; resize:vertical; min-height:80px; font-size:14px; margin-bottom:12px;"
      ></textarea>
      <button @click="handleCreate" :disabled="!newTitle.trim() || creating">
        {{ creating ? 'Guardando...' : '+ Agregar nota' }}
      </button>
    </div>

    <!-- Lista de notas -->
    <div v-if="loading" style="text-align: center; color: #888;">Cargando notas...</div>

    <div v-else-if="notes.length === 0" style="text-align: center; color: #888;">
      No tenés notas todavía. ¡Creá la primera!
    </div>

    <div v-else>
      <div
        v-for="note in notes"
        :key="note.id"
        style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); display: flex; justify-content: space-between; align-items: flex-start;"
      >
        <div>
          <strong>{{ note.title }}</strong>
          <p v-if="note.content" style="font-size: 14px; color: #666; margin-top: 4px;">{{ note.content }}</p>
          <small style="color: #aaa;">{{ formatDate(note.created_at) }}</small>
        </div>
        <button
          @click="handleDelete(note.id)"
          style="background: #ef4444; margin-left: 16px; flex-shrink: 0;"
        >
          Eliminar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { notesService } from '../services/api'

const notes = ref([])
const loading = ref(true)
const creating = ref(false)
const newTitle = ref('')
const newContent = ref('')

async function loadNotes() {
  loading.value = true
  try {
    const res = await notesService.getAll()
    notes.value = res.data.notes
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newTitle.value.trim()) return
  creating.value = true
  try {
    const res = await notesService.create(newTitle.value, newContent.value)
    notes.value.unshift(res.data.note)  // Agregar al inicio de la lista
    newTitle.value = ''
    newContent.value = ''
  } finally {
    creating.value = false
  }
}

async function handleDelete(id) {
  await notesService.delete(id)
  notes.value = notes.value.filter(n => n.id !== id)
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

onMounted(loadNotes)
</script>
