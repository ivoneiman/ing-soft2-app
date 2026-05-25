import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";
const REQUEST_CONFIG = { withCredentials: true };

// =========================
// AUTH
// =========================

export function register({ username, apellido, email, dni, telefono, password }) {
  return axios.post(`${API_URL}/register`, { username, apellido, email, dni, telefono, password }, REQUEST_CONFIG);
}

export function crearUsuario({ username, apellido, email, dni, telefono, password }) {
  return axios.post(`${API_URL}/users`, { username, apellido, email, dni, telefono, password }, REQUEST_CONFIG);
}

export function login({ email, password, remember }) {
  return axios.post(
    `${API_URL}/login`,
    { email, password, remember },
    REQUEST_CONFIG
  );
}

export function logout() {
  return axios.post(
    `${API_URL}/logout`,
    {},
    REQUEST_CONFIG
  );
}

export function getCurrentUser() {
  return axios.get(
    `${API_URL}/me`,
    REQUEST_CONFIG
  );
}

// =========================
// ACTIVIDADES
// =========================

export function getActivities() {
  return axios.get(
    `${API_URL}/actividades`,
    REQUEST_CONFIG
  );
}

export function getActivityClasses(actividad_id) {
  return axios.get(
    `${API_URL}/actividades/${actividad_id}/classes`,
    REQUEST_CONFIG
  );
}

// =========================
// CATÁLOGO
// =========================

export function getAllClasses() {
  return axios.get(
    `${API_URL}/classes/all`,
    REQUEST_CONFIG
  );
}

export function getCatalogAvailability(actividad_id, fecha) {
  return axios.get(
    `${API_URL}/catalog/availability`,
    {
      params: { actividad_id, fecha },
      ...REQUEST_CONFIG,
    }
  );
}

export function getCatalogDays(actividad_id, year, month) {
  return axios.get(
    `${API_URL}/catalog/days`,
    {
      params: { actividad_id, year, month },
      ...REQUEST_CONFIG,
    }
  );
}

// =========================
// CLASES
// =========================

export function createClass({
  activity_id,
  date,
  time,
  cupoMaximo,
  tipo = "individual",
}) {
  return axios.post(
    `${API_URL}/classes`,
    {
      activity_id,
      date,
      time,
      cupoMaximo,
      tipo,
    },
    REQUEST_CONFIG
  );
}

// =========================
// ASISTENCIA
// =========================

export function registerAttendance({
  user_id,
  class_id,
}) {
  return axios.post(
    `${API_URL}/attendance/register`,
    { user_id, class_id },
    REQUEST_CONFIG
  );
}

// =========================
// CANCELACIONES
// =========================

export function cancelarClaseCompleta(clase_id) {
  return axios.post(
    `${API_URL}/classes/${clase_id}/cancelar`,
    {},
    REQUEST_CONFIG
  );
}

export function createEnrollment({ class_id, tipo }) {
  return axios.post(
    `${API_URL}/enrollments`,
    { class_id, tipo },
    REQUEST_CONFIG
  );
}

export function getPendingEnrollments(testDay) {
  return axios.get(
    `${API_URL}/enrollments/pending`,
    {
      params: testDay ? { test_day: testDay } : {},
      ...REQUEST_CONFIG,
    }
  );
}

// PAGOS
// =========================

export function createPayment({
  payment_method,
  enrollment_id,
}) {
  return axios.post(
    `${API_URL}/payments/create`,
    {
      payment_method,
      enrollment_id,
    },
    REQUEST_CONFIG
  );
}

export function getPaymentHistory() {
  return axios.get(
    `${API_URL}/payments/history`,
    REQUEST_CONFIG
  );
}

export function getPaymentDiscountRules(testDay) {
  return axios.get(
    `${API_URL}/payments/discount-rules`,
    {
      params: testDay ? { test_day: testDay } : {},
      ...REQUEST_CONFIG,
    }
  );
}

export function applyClassDiscount(classId, descuento) {
  return axios.put(
    `${API_URL}/classes/${classId}/discount`,
    { descuento },
    REQUEST_CONFIG
  );
}
