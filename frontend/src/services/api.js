import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";
const REQUEST_CONFIG = { withCredentials: true };

// =========================
// AUTH
// =========================

export function register({ username, apellido, email, dni, telefono, password }) {
  return axios.post(`${API_URL}/register`, { username, apellido, email, dni, telefono, password }, REQUEST_CONFIG);
}

export function crearUsuario({ username, apellido, email, dni, telefono, password, role }) {
  return axios.post(`${API_URL}/users`, { username, apellido, email, dni, telefono, password, role }, REQUEST_CONFIG);
}

export function getUsers() {
  return axios.get(`${API_URL}/users`, REQUEST_CONFIG);
}

export function login({ email, password, remember }) {
  return axios.post(
    `${API_URL}/login`,
    { email, password, remember },
    REQUEST_CONFIG
  );
}

export function adminLoginRequest({ email, password }) {
  return axios.post(
    `${API_URL}/admin-login/request`,
    { email, password },
    REQUEST_CONFIG
  );
}

export function adminLoginVerify({ email, code }) {
  return axios.post(
    `${API_URL}/admin-login/verify`,
    { email, code },
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

export function updateProfile({ username, apellido, telefono, dni }) {
  return axios.put(
    `${API_URL}/me`,
    { username, apellido, telefono, dni },
    REQUEST_CONFIG
  );
}

export function changePassword({ current_password, new_password, confirm_password }) {
  return axios.post(
    `${API_URL}/me/change-password`,
    { current_password, new_password, confirm_password },
    REQUEST_CONFIG
  );
}

export function deleteAccount({ password }) {
  return axios.delete(
    `${API_URL}/me`,
    {
      ...REQUEST_CONFIG,
      data: { password } // 💡 Aquí se agrega la contraseña al cuerpo de la petición
    }
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

export function getCatalog() {
  return axios.get(
    `${API_URL}/catalog`,
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

export function getMyClasses() {
  return axios.get(
    `${API_URL}/classes/my`,
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

export function getClassAttendance(classId) {
  return axios.get(
    `${API_URL}/classes/${classId}/attendance`,
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

// =========================
// CONFIGURACIONES
// =========================

export function getNotificationConfig() {
  return axios.get(
    `${API_URL}/settings/notification-message`,
    REQUEST_CONFIG
  );
}

export function saveNotificationConfig(message) {
  return axios.put(
    `${API_URL}/settings/notification-message`,
    { message },
    REQUEST_CONFIG
  );
}

export function createEnrollment({ class_id, tipo, waitlist, waitlist_type }) {
  return axios.post(
    `${API_URL}/enrollments`,
    { class_id, tipo, waitlist, waitlist_type },
    REQUEST_CONFIG
  );
}

export function createWaitlist({ class_id, type }) {
  return axios.post(
    `${API_URL}/waitlists`,
    { class_id, type },
    REQUEST_CONFIG
  );
}

export function cancelEnrollment({ enrollment_id }) {
  return axios.post(
    `${API_URL}/enrollments/${enrollment_id}/cancel`,
    {},
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
  payment_type,
}) {
  return axios.post(
    `${API_URL}/payments/create`,
    {
      payment_method,
      enrollment_id,
      payment_type,
    },
    REQUEST_CONFIG
  );
}

export function getAdminPaymentEnrollments() {
  return axios.get(
    `${API_URL}/admin/enrollments/payments`,
    REQUEST_CONFIG
  );
}

export function registerManualPayment(enrollmentId, {
  amount,
  payment_method,
  payment_type,
  notes,
}) {
  return axios.post(
    `${API_URL}/enrollments/${enrollmentId}/manual-payment`,
    {
      amount,
      payment_method,
      payment_type,
      notes,
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

export function getMyCredits() {
  return axios.get(
    `${API_URL}/credits/my`,
    REQUEST_CONFIG
  );
}

export function getMyNotifications() {
  return axios.get(
    `${API_URL}/notifications/my`,
    REQUEST_CONFIG
  );
}

export function applyClassDiscount(classId, descuento) {
  return axios.put(
    `${API_URL}/classes/${classId}/discount`,
    { descuento },
    REQUEST_CONFIG
  );
}
