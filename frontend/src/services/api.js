import axios from "axios";

const API_URL = "http://localhost:5000/api";

console.log("API_URL EN PRODUCCION:", API_URL);

// =========================
// AUTH
// =========================

export function register({ username, apellido, email, dni, telefono, password }) {
  return axios.post(`${API_URL}/register`, { username, apellido, email, dni, telefono, password }, { withCredentials: true });
}

export function crearUsuario({ username, apellido, email, dni, telefono, password }) {
  return axios.post(`${API_URL}/users`, { username, apellido, email, dni, telefono, password }, { withCredentials: true });
}

export function login({ email, password, remember }) {
  return axios.post(
    `${API_URL}/login`,
    { email, password, remember },
    { withCredentials: true }
  );
}

export function logout() {
  return axios.post(
    `${API_URL}/logout`,
    {},
    { withCredentials: true }
  );
}

export function getCurrentUser() {
  return axios.get(
    `${API_URL}/me`,
    { withCredentials: true }
  );
}

// =========================
// ACTIVIDADES
// =========================

export function getActivities() {
  return axios.get(
    `${API_URL}/actividades`,
    { withCredentials: true }
  );
}

export function getActivityClasses(actividad_id) {
  return axios.get(
    `${API_URL}/actividades/${actividad_id}/classes`,
    { withCredentials: true }
  );
}

export function getPaymentClasses(testDay) {
  return axios.get(
    `${API_URL}/classes`,
    {
      params: testDay ? { test_day: testDay } : {},
      withCredentials: true,
    }
  );
}

// =========================
// CATÁLOGO
// =========================

export function getAvailableClasses() {
  return axios.get(
    `${API_URL}/catalog`,
    { withCredentials: true }
  );
}

export function getCatalogAvailability(actividad_id, fecha) {
  return axios.get(
    `${API_URL}/catalog/availability`,
    {
      params: { actividad_id, fecha },
      withCredentials: true,
    }
  );
}

export function getCatalogDays(actividad_id, year, month) {
  return axios.get(
    `${API_URL}/catalog/days`,
    {
      params: { actividad_id, year, month },
      withCredentials: true,
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
  cupoMaximo
}) {
  return axios.post(
    `${API_URL}/classes`,
    {
      activity_id,
      date,
      time,
      cupoMaximo
    },
    { withCredentials: true }
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
    { withCredentials: true }
  );
}

// =========================
// PAGOS
// =========================

export function createPayment({
  payment_type,
  payment_method,
  class_id,
  payment_option,
}) {
  return axios.post(
    `${API_URL}/payments/create`,
    {
      payment_type,
      payment_method,
      class_id,
      payment_option,
    },
    { withCredentials: true }
  );
}

export function getPaymentHistory() {
  return axios.get(
    `${API_URL}/payments/history`,
    { withCredentials: true }
  );
}
