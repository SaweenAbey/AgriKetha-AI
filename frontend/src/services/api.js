import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request interceptor to add Authorization token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("agriketha_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling 401 & token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("agriketha_refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newToken = res.data.access_token;
          localStorage.setItem("agriketha_token", newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem("agriketha_token");
          localStorage.removeItem("agriketha_refresh_token");
          localStorage.removeItem("agriketha_user");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (email, password) => {
    const response = await api.post("/auth/login", { email, password });
    return response.data;
  },
  register: async (userData) => {
    const response = await api.post("/auth/register", userData);
    return response.data;
  },
  getProfile: async () => {
    const response = await api.get("/auth/me");
    return response.data;
  },
};

export const agentService = {
  queryAgent1: async ({ question, input_mode = "text", auto_triggered = false, language = "en" }) => {
    const response = await api.post("/farmer/query-agent", {
      question,
      input_mode,
      auto_triggered,
      language,
    });
    return response.data;
  },
  getQueryHistory: async (limit = 20) => {
    const response = await api.get(`/farmer/queries?limit=${limit}`);
    return response.data;
  },
  checkAgentStatus: async () => {
    const response = await api.get("/farmer/agent-1-status");
    return response.data;
  },
};

export const visionService = {
  analyzeImage: async (formData) => {
    const response = await api.post("/farmer/vision/analyze", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 30000,
    });
    return response.data;
  },
  getDiagnosticHistory: async (limit = 20) => {
    const response = await api.get(`/farmer/vision/history?limit=${limit}`);
    return response.data;
  },
  checkVisionStatus: async () => {
    const response = await api.get("/farmer/vision/status");
    return response.data;
  },
};

export default api;


