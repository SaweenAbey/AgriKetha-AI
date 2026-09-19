import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { userService } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

const QuotaContext = createContext(null);

export const QuotaProvider = ({ children }) => {
  const { user } = useAuth();
  const [quota, setQuota] = useState({
    plan: "free",
    is_unlimited: false,
    text: { used: 0, limit: 25, remaining: 25, unlimited: false },
    image: { used: 0, limit: 5, remaining: 5, unlimited: false },
    voice: { used: 0, limit: 5, remaining: 5, unlimited: false },
  });
  const [loading, setLoading] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  const fetchQuota = useCallback(async () => {
    if (!localStorage.getItem("agriketha_token")) return;
    try {
      setLoading(true);
      const data = await userService.getQuota();
      if (data) {
        setQuota(data);
      }
    } catch (err) {
      console.warn("Quota fetch notice:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchQuota();
    }
  }, [user, fetchQuota]);

  const updateQuotaFromResponse = (newQuota) => {
    if (newQuota) {
      setQuota(newQuota);
    }
  };

  const upgradePlan = async (targetPlan = "premium") => {
    try {
      setLoading(true);
      const res = await userService.upgradeSubscription(targetPlan);
      if (res?.quota) {
        setQuota(res.quota);
      }
      return { success: true, message: res?.message };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || "Upgrade failed" };
    } finally {
      setLoading(false);
    }
  };

  return (
    <QuotaContext.Provider
      value={{
        quota,
        loading,
        fetchQuota,
        upgradePlan,
        updateQuotaFromResponse,
        showUpgradeModal,
        setShowUpgradeModal,
        isUnlimited: quota?.is_unlimited || quota?.plan === "premium" || user?.role === "admin",
      }}
    >
      {children}
    </QuotaContext.Provider>
  );
};

export const useQuota = () => {
  const context = useContext(QuotaContext);
  if (!context) {
    throw new Error("useQuota must be used within a QuotaProvider");
  }
  return context;
};
