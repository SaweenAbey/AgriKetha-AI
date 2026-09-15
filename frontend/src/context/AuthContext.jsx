import React, { createContext, useContext, useState, useEffect } from "react";
import { authService } from "@/services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("agriketha_user");
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("agriketha_token") || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync token state to localStorage
  useEffect(() => {
    if (token) {
      localStorage.setItem("agriketha_token", token);
    } else {
      localStorage.removeItem("agriketha_token");
    }
  }, [token]);

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.login(email, password);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem("agriketha_token", data.access_token);
      localStorage.setItem("agriketha_refresh_token", data.refresh_token);
      localStorage.setItem("agriketha_user", JSON.stringify(data.user));
      return { success: true, data };
    } catch (err) {
      const message = err.response?.data?.detail || "Invalid email or password. Please try again.";
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.register(userData);
      // Auto-login after registration or return success
      return { success: true, data };
    } catch (err) {
      const message = err.response?.data?.detail || "Registration failed. Please check your details.";
      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("agriketha_token");
    localStorage.removeItem("agriketha_refresh_token");
    localStorage.removeItem("agriketha_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        loading,
        error,
        setError,
        login,
        register,
        logout,
        setUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
