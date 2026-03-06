import axios from 'axios'

// Con el proxy de Vite, no hace falta poner la URL completa
// Las llamadas a /api se redirigen automáticamente a http://localhost:5000
const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // Necesario para que las cookies de sesión viajen
  headers: { 'Content-Type': 'application/json' }
})

// Interceptor para manejar errores globalmente
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Si el backend devuelve 401, redirigir al login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authService = {
  register: (username, email, password) =>
    api.post('/register', { username, email, password }),

  login: (email, password) =>
    api.post('/login', { email, password }),

  logout: () =>
    api.post('/logout'),

  me: () =>
    api.get('/me'),
}

export const notesService = {
  getAll: () => api.get('/notes'),
  create: (title, content) => api.post('/notes', { title, content }),
  delete: (id) => api.delete(`/notes/${id}`),
}

export default api
