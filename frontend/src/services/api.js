import axios from "axios";

const API_URL = "http://localhost:5000/api";
console.log("API_URL EN PRODUCCION:", API_URL);

export function register({ username, email, password }) {
  return axios.post(`${API_URL}/register`, { username, email, password }, { withCredentials: true });
}

export function login({ email, password, remember }) {
  return axios.post(`${API_URL}/login`, { email, password, remember }, { withCredentials: true });
}

export function logout() {
  return axios.post(`${API_URL}/logout`, {}, { withCredentials: true });
}

export function getCurrentUser() {
  return axios.get(`${API_URL}/me`, { withCredentials: true });
}
