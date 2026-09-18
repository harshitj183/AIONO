import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("aiono_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("aiono_token");
      localStorage.removeItem("aiono_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Auth ──────────────────────────────────────────────────────

export async function login(username: string, password: string) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await api.post("/api/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
}

export async function getMe() {
  const res = await api.get("/api/auth/me");
  return res.data;
}

// ── Investigations ────────────────────────────────────────────

export async function submitInvestigation(question: string) {
  const res = await api.post("/api/investigations", { question });
  return res.data;
}

export async function getInvestigation(id: number) {
  const res = await api.get(`/api/investigations/${id}`);
  return res.data;
}

export async function listInvestigations(limit = 20, offset = 0) {
  const res = await api.get(`/api/investigations?limit=${limit}&offset=${offset}`);
  return res.data;
}

export async function deleteInvestigation(id: number) {
  const res = await api.delete(`/api/investigations/${id}`);
  return res.data;
}

// ── Analytics ─────────────────────────────────────────────────

export async function getDashboardMetrics() {
  const res = await api.get("/api/analytics/dashboard");
  return res.data;
}

export async function checkHealth() {
  const res = await api.get("/health");
  return res.data;
}
