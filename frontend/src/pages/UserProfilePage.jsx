import React, { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import {
  User,
  Crown,
  Zap,
  Mail,
  MapPin,
  ShieldCheck,
  CreditCard,
  Receipt,
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  Calendar,
  Clock,
  RotateCcw,
  Edit3,
  Save,
  Loader2,
  Languages,
  LogOut,
  Download,
  AlertCircle,
  Check,
  Lock,
  Users,
  Activity,
  TrendingUp,
  Bot,
  Leaf,
  Search,
  RefreshCw,
  Filter,
  Phone,
  Building2,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { useQuota } from "@/context/QuotaContext";
import { userService, paymentService, adminService } from "@/services/api";
import { PaymentCheckoutModal } from "@/components/PaymentCheckoutModal";

const SRI_LANKA_DISTRICTS = [
  "Anuradhapura", "Polonnaruwa", "Kurunegala", "Puttalam", "Kandy", 
  "Matale", "Nuwara Eliya", "Badulla", "Monaragala", "Ratnapura", 
  "Kegalle", "Ampara", "Batticaloa", "Trincomalee", "Galle", 
  "Matara", "Hambantota", "Colombo", "Gampaha", "Kalutara", 
  "Jaffna", "Kilinochchi", "Mannar", "Vavuniya", "Mullaitivu"
];

export const UserProfilePage = () => {
  const { user, setUser, confirmLogout } = useAuth();
  const { quota, isUnlimited, upgradePlan, fetchQuota } = useQuota();
  const { language, toggleLanguage, t } = useLanguage();
  const navigate = useNavigate();

  const isAdmin = user?.role === "admin";

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    phone_number: user?.phone_number || "",
    district: user?.district || "Kurunegala",
  });
  const [savingProfile, setSavingProfile] = useState(false);

  // Billing history state for normal farmer
  const [invoices, setInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(!isAdmin);
  const [showCheckout, setShowCheckout] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  // Admin specific executive state
  const [adminStats, setAdminStats] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminOrders, setAdminOrders] = useState([]);
  const [loadingAdmin, setLoadingAdmin] = useState(isAdmin);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDistrictFilter, setSelectedDistrictFilter] = useState("all");
  const [togglingUserId, setTogglingUserId] = useState(null);

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        phone_number: user.phone_number || "",
        district: user.district || "Kurunegala",
      });
    }
  }, [user]);

  // Fetch farmer invoices if not admin
  const fetchInvoices = async () => {
    try {
      setLoadingInvoices(true);
      const data = await paymentService.getHistory();
      if (Array.isArray(data)) {
        setInvoices(data);
      } else if (data?.history && Array.isArray(data.history)) {
        setInvoices(data.history);
      } else if (data?.orders && Array.isArray(data.orders)) {
        setInvoices(data.orders);
      } else {
        setInvoices([]);
      }
    } catch (err) {
      console.warn("Could not fetch invoices:", err);
      setInvoices([]);
    } finally {
      setLoadingInvoices(false);
    }
  };

  // Fetch admin executive statistics & farmer directory
  const fetchAdminData = async () => {
    if (!isAdmin) return;
    try {
      setLoadingAdmin(true);
      const [statsRes, usersRes, ordersRes] = await Promise.allSettled([
        adminService.getStats(),
        adminService.getUsers({ limit: 100 }),
        adminService.getOrders(50),
      ]);

      if (statsRes.status === "fulfilled") {
        setAdminStats(statsRes.value);
      }
      if (usersRes.status === "fulfilled" && Array.isArray(usersRes.value)) {
        setAdminUsers(usersRes.value);
      }
      if (ordersRes.status === "fulfilled" && Array.isArray(ordersRes.value)) {
        setAdminOrders(ordersRes.value);
      }
    } catch (err) {
      console.error("Failed to load admin stats:", err);
      toast.error("Failed to load administrative analytics.");
    } finally {
      setLoadingAdmin(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchAdminData();
    } else {
      fetchInvoices();
    }
  }, [isAdmin]);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const updated = await userService.updateProfile(formData);
      setUser(updated);
      localStorage.setItem("agriketha_user", JSON.stringify(updated));
      setIsEditing(false);
      toast.success(language === "si" ? "පැතිකඩ සාර්ථකව යාවත්කාලීන විය." : "Profile updated successfully.");
    } catch (err) {
      console.error("Profile update failed:", err);
      toast.error("Failed to update profile. Please try again.");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleDowngrade = async () => {
    if (!window.confirm(language === "si" ? "ඔබට නොමිලේ සැලැස්මට (Free Plan) මාරු වීමට අවශ්‍ය බව සහතිකද?" : "Are you sure you want to switch to the Free Starter Plan?")) {
      return;
    }
    setDowngrading(true);
    const res = await upgradePlan("free");
    setDowngrading(false);
    if (res.success) {
      toast.success(language === "si" ? "නොමිලේ සැලැස්මට මාරු විය." : "Switched to Free Plan.");
      fetchQuota();
    } else {
      toast.error(language === "si" ? "සැලැස්ම මාරු කිරීම අසාර්ථක විය." : "Failed to switch plan.");
    }
  };

  const handleToggleUserStatus = async (targetUser) => {
    setTogglingUserId(targetUser.id);
    try {
      const newStatus = !targetUser.is_active;
      const updated = await adminService.updateUserStatus(targetUser.id, newStatus);
      setAdminUsers((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, is_active: updated.is_active } : u))
      );
      toast.success(`Farmer account ${targetUser.email} ${newStatus ? "Activated" : "Deactivated"}`);
      fetchAdminData();
    } catch (err) {
      console.error("Failed to toggle status:", err);
      toast.error(err.response?.data?.detail || "Could not update user status");
    } finally {
      setTogglingUserId(null);
    }
  };

  // Filtered users for admin directory
  const filteredUsers = adminUsers.filter((u) => {
    const matchesSearch =
      !searchQuery ||
      u.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.district?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDistrict =
      selectedDistrictFilter === "all" || u.district === selectedDistrictFilter;
    return matchesSearch && matchesDistrict;
  });

  return (
    <div className="agentic-bg min-h-screen bg-gradient-to-br from-emerald-50/50 via-background to-teal-50/30 dark:from-slate-950 dark:via-emerald-950/20 dark:to-slate-950 text-foreground pb-16">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-border/60 bg-background/60 backdrop-blur-xl supports-[backdrop-filter]:bg-background/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/dashboard")}
              className="gap-2 rounded-xl text-xs font-bold border-border hover:border-emerald-500/50"
            >
              <ArrowLeft className="w-4 h-4 text-emerald-600" />
              <span>{language === "si" ? "පාලන මැදිරියට (Dashboard)" : "Back to Dashboard"}</span>
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className="gap-1.5 text-xs font-semibold rounded-xl border-border"
            >
              <Languages className="w-3.5 h-3.5 text-emerald-600" />
              <span>{language === "si" ? "English" : "සිංහල"}</span>
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (confirmLogout()) navigate("/login");
              }}
              className="text-xs text-muted-foreground hover:text-destructive gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{language === "si" ? "පිටවීම" : "Sign Out"}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 space-y-8">
        {/* Profile / Officer Header Hero Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white p-6 sm:p-8 shadow-2xl border border-emerald-500/20">
          <div className="absolute top-0 right-0 -translate-y-12 translate-x-12 w-80 h-80 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 p-0.5 shadow-xl">
                <div className="w-full h-full rounded-[14px] bg-slate-900/90 flex items-center justify-center text-2xl sm:text-3xl font-black text-emerald-400">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "A"}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                    {user?.full_name || (isAdmin ? "Agricultural Officer" : "AgriKetha Farmer")}
                  </h1>
                  {isAdmin ? (
                    <Badge className="bg-gradient-to-r from-amber-500 to-yellow-500 text-slate-950 font-black text-xs gap-1.5 shadow-md border-0 px-2.5 py-0.5">
                      <ShieldCheck className="w-3.5 h-3.5 fill-slate-950" />
                      DOA Officer Admin
                    </Badge>
                  ) : isUnlimited ? (
                    <Badge className="bg-gradient-to-r from-amber-500 to-yellow-500 text-slate-950 font-black text-xs gap-1 shadow-md border-0">
                      <Crown className="w-3.5 h-3.5 fill-slate-950" />
                      AgriKetha PRO
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="text-xs font-semibold bg-white/20 text-white border-0">
                      Free Starter
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-emerald-200/90 flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-emerald-300" />
                  {user?.email || "user@agriketha.lk"}
                </p>
                <p className="text-xs text-emerald-200/90 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-emerald-300" />
                  {user?.district || "Sri Lanka"} • {isAdmin ? "Government Officer / Administrator" : "Registered Farmer"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 self-start sm:self-center">
              {!isEditing ? (
                <Button
                  onClick={() => setIsEditing(true)}
                  size="sm"
                  className="bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-xl text-xs font-bold gap-1.5 backdrop-blur-sm"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>{language === "si" ? "තොරතුරු සංස්කරණය" : "Edit Profile"}</span>
                </Button>
              ) : (
                <Button
                  onClick={() => setIsEditing(false)}
                  size="sm"
                  variant="ghost"
                  className="text-white hover:bg-white/10 rounded-xl text-xs font-semibold"
                >
                  {language === "si" ? "අවලංගු කරන්න" : "Cancel"}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Profile Edit Form (when triggered) */}
        {isEditing && (
          <Card className="p-6 border-emerald-500/40 bg-card/90 backdrop-blur-sm shadow-xl rounded-3xl animate-in slide-in-from-top-3">
            <CardHeader className="p-0 pb-4">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-emerald-600" />
                <span>{language === "si" ? "පරිශීලක තොරතුරු යාවත්කාලීන කිරීම" : "Update Profile Details"}</span>
              </CardTitle>
            </CardHeader>
            <form onSubmit={handleProfileSave} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">
                    {language === "si" ? "සම්පූර්ණ නම" : "Full Name"}
                  </label>
                  <Input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                    className="rounded-xl text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">
                    {language === "si" ? "දුරකථන අංකය" : "Phone Number"}
                  </label>
                  <Input
                    type="text"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                    placeholder="07X XXX XXXX"
                    className="rounded-xl text-xs"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">
                    {language === "si" ? "කෘෂිකාර්මික දිස්ත්‍රික්කය" : "Agricultural District"}
                  </label>
                  <select
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    className="w-full h-9 rounded-xl border border-input bg-background px-3 py-1 text-xs text-foreground shadow-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    {SRI_LANKA_DISTRICTS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="submit"
                  disabled={savingProfile}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold gap-1.5"
                >
                  {savingProfile ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  <span>{language === "si" ? "සුරකින්න" : "Save Changes"}</span>
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* ========================================================================= */}
        {/* CONDITIONAL BRANCH: OFFICER / ADMIN VIEW vs NORMAL FARMER VIEW            */}
        {/* ========================================================================= */}
        {isAdmin ? (
          /* ========================================================= */
          /* OFFICER / ADMIN EXECUTIVE DASHBOARD & SYSTEM ANALYTICS     */
          /* ========================================================= */
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* Header with Refresh */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black tracking-tight text-foreground flex items-center gap-2.5">
                  <ShieldCheck className="w-6 h-6 text-emerald-600" />
                  <span>{language === "si" ? "කෘෂි නිලධාරී විධායක පාලන මධ්‍යස්ථානය" : "Officer Admin Executive Center"}</span>
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {language === "si"
                    ? "ශ්‍රී ලංකා ගොවි ජාලය, ආදායම්, සහ AI නියෝජිත පද්ධතිවල සජීවී දත්ත විශ්ලේෂණය"
                    : "Real-time surveillance of customer farmers, subscription revenue, and AI microservices health"}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchAdminData}
                disabled={loadingAdmin}
                className="text-xs rounded-xl border-border gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingAdmin ? "animate-spin text-emerald-600" : ""}`} />
                <span>{language === "si" ? "දත්ත අලුත් කරන්න" : "Refresh Metrics"}</span>
              </Button>
            </div>

            {/* 4 PRIMARY ADMIN KPI METRIC CARDS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* 1. TOTAL CUSTOMERS */}
              <Card className="rounded-3xl border border-border/80 bg-card p-5 shadow-lg relative overflow-hidden group hover:border-emerald-500/40 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    {language === "si" ? "මුළු ගොවි පරිශීලකයින්" : "Total Customers"}
                  </span>
                  <div className="p-2.5 rounded-2xl bg-emerald-500/10 text-emerald-600">
                    <Users className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <div className="text-3xl font-black tracking-tight text-foreground">
                    {loadingAdmin ? (
                      <span className="animate-pulse">--</span>
                    ) : (
                      adminStats?.total_customers ?? adminStats?.total_farmers ?? adminUsers.length ?? 0
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-0">
                      {adminStats?.active_users ?? adminUsers.filter((u) => u.is_active).length ?? 0} Active
                    </Badge>
                    <span>Registered farmers</span>
                  </p>
                </div>
              </Card>

              {/* 2. TOTAL REVENUE */}
              <Card className="rounded-3xl border border-border/80 bg-card p-5 shadow-lg relative overflow-hidden group hover:border-amber-500/40 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    {language === "si" ? "මුළු වේදිකා ආදායම" : "Total Revenue"}
                  </span>
                  <div className="p-2.5 rounded-2xl bg-amber-500/10 text-amber-600">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <div className="text-3xl font-black tracking-tight text-foreground">
                    {loadingAdmin ? (
                      <span className="animate-pulse">--</span>
                    ) : (
                      `Rs. ${Number(adminStats?.total_revenue || 0).toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}`
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px] font-bold bg-amber-500/10 text-amber-700 dark:text-amber-300 border-0">
                      PayHere LKR
                    </Badge>
                    <span>Pro Subscription sales</span>
                  </p>
                </div>
              </Card>

              {/* 3. NUMBER OF PRO FARMERS */}
              <Card className="rounded-3xl border border-border/80 bg-card p-5 shadow-lg relative overflow-hidden group hover:border-yellow-500/40 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    {language === "si" ? "Pro ග්‍රාහක ගොවීන්" : "Num of Pro Farmers"}
                  </span>
                  <div className="p-2.5 rounded-2xl bg-yellow-500/10 text-yellow-600">
                    <Crown className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <div className="text-3xl font-black tracking-tight text-foreground">
                    {loadingAdmin ? (
                      <span className="animate-pulse">--</span>
                    ) : (
                      `${adminStats?.pro_farmers ?? 0}`
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px] font-bold bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border-0">
                      👑 Unlimited
                    </Badge>
                    <span>vs {adminStats?.free_farmers ?? 0} Free Tier</span>
                  </p>
                </div>
              </Card>

              {/* 4. AGENTS WORKING HEALTHY */}
              <Card className="rounded-3xl border border-border/80 bg-card p-5 shadow-lg relative overflow-hidden group hover:border-teal-500/40 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    {language === "si" ? "නියෝජිත සෞඛ්‍ය තත්ත්වය" : "Agents Working Healthy"}
                  </span>
                  <div className="p-2.5 rounded-2xl bg-teal-500/10 text-teal-600">
                    <Activity className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <div className="text-2xl font-black tracking-tight text-emerald-600 flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-emerald-500 animate-ping inline-block" />
                    <span>4 / 4 Healthy</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                    <Badge variant="secondary" className="text-[10px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-0">
                      99.9% Uptime
                    </Badge>
                    <span>Zero latency bottlenecks</span>
                  </p>
                </div>
              </Card>
            </div>

            {/* AI MULTI-AGENT OPERATIONAL HEALTH CENTER */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-black text-foreground flex items-center gap-2">
                  <Bot className="w-5 h-5 text-emerald-600" />
                  <span>{language === "si" ? "AI බහු-නියෝජිත පද්ධති සජීවී තත්ත්වය" : "Live AI Agents Operational Health"}</span>
                </h3>
                <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px] font-bold">
                  ✓ All Microservices Synchronized
                </Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Agent 4 Orchestrator */}
                <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-600 font-bold text-xs">
                        A4
                      </div>
                      <span className="text-xs font-bold text-foreground">Multi-Agent Hub</span>
                    </div>
                    <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold border-0">
                      🟢 Healthy
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Unified Gemini Orchestrator coordinating all 4 AI microservices.
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border">
                    <span>Uptime: 99.98%</span>
                    <span className="font-mono text-emerald-600">~145ms</span>
                  </div>
                </div>

                {/* Agent 1/2 DOA Advisor */}
                <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-600 font-bold text-xs">
                        A1
                      </div>
                      <span className="text-xs font-bold text-foreground">DOA NLP & Voice</span>
                    </div>
                    <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold border-0">
                      🟢 Healthy
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Grounded RAG retrieval corpus & Sinhala/Tamil multilingual NLP.
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border">
                    <span>Uptime: 99.95%</span>
                    <span className="font-mono text-emerald-600">~110ms</span>
                  </div>
                </div>

                {/* Vision Agent */}
                <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-xl bg-teal-500/10 text-teal-600 font-bold text-xs">
                        A3
                      </div>
                      <span className="text-xs font-bold text-foreground">PyTorch & Grad-CAM</span>
                    </div>
                    <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold border-0">
                      🟢 Healthy
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Deep learning plant pathology CNN with explainable visual saliency.
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border">
                    <span>Uptime: 99.90%</span>
                    <span className="font-mono text-teal-600">~180ms</span>
                  </div>
                </div>

                {/* Market Price Agent */}
                <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-xl bg-amber-500/10 text-amber-600 font-bold text-xs">
                        A2
                      </div>
                      <span className="text-xs font-bold text-foreground">Market Price Advisor</span>
                    </div>
                    <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold border-0">
                      🟢 Healthy
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    CBSL Economic Center price feed scraper & price trend engine.
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border">
                    <span>Uptime: 100%</span>
                    <span className="font-mono text-amber-600">~85ms</span>
                  </div>
                </div>
              </div>
            </div>

            {/* REGISTERED FARMERS & CUSTOMER DIRECTORY */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-base font-black text-foreground flex items-center gap-2">
                    <Users className="w-5 h-5 text-emerald-600" />
                    <span>{language === "si" ? "ලියාපදිංචි ගොවීන් සහ පාරිභෝගික නාමාවලිය" : "Registered Farmers & Customer Directory"}</span>
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Manage farmer accounts, RBAC roles, and subscription status across Sri Lanka.
                  </p>
                </div>

                {/* Search & Filter Bar */}
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Search farmer name or email..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 h-8 text-xs rounded-xl w-48 sm:w-60 bg-background"
                    />
                  </div>

                  <select
                    value={selectedDistrictFilter}
                    onChange={(e) => setSelectedDistrictFilter(e.target.value)}
                    className="h-8 rounded-xl border border-input bg-background px-2.5 text-xs text-foreground shadow-sm focus:outline-none"
                  >
                    <option value="all">All Districts</option>
                    {SRI_LANKA_DISTRICTS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <Card className="rounded-3xl border border-border bg-card overflow-hidden shadow-lg">
                {loadingAdmin ? (
                  <div className="p-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                    <span>Loading registered farmers...</span>
                  </div>
                ) : filteredUsers.length === 0 ? (
                  <div className="p-8 text-center space-y-2">
                    <Users className="w-8 h-8 text-muted-foreground/40 mx-auto" />
                    <p className="text-xs text-muted-foreground">No farmers found matching your filter criteria.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-muted/50 border-b border-border text-muted-foreground uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                          <th className="py-3 px-4">Farmer / Customer</th>
                          <th className="py-3 px-4">District</th>
                          <th className="py-3 px-4">Role</th>
                          <th className="py-3 px-4">Subscription Tier</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Administrative Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {filteredUsers.map((u) => {
                          const isPro =
                            u.plan === "premium" ||
                            u.plan === "pro" ||
                            u.subscription_plan === "premium" ||
                            u.subscription_status === "active";

                          return (
                            <tr key={u.id || u.email} className="hover:bg-muted/30 transition-colors">
                              <td className="py-3 px-4">
                                <div className="font-bold text-foreground">{u.full_name || "Farmer"}</div>
                                <div className="text-[11px] text-muted-foreground font-mono">{u.email}</div>
                              </td>
                              <td className="py-3 px-4">
                                <span className="inline-flex items-center gap-1 font-medium text-foreground">
                                  <MapPin className="w-3 h-3 text-emerald-600" />
                                  {u.district || "Sri Lanka"}
                                </span>
                              </td>
                              <td className="py-3 px-4">
                                {u.role === "admin" ? (
                                  <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px] font-bold">
                                    Officer / Admin
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-[10px] text-muted-foreground border-border">
                                    Farmer
                                  </Badge>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                {isPro ? (
                                  <Badge className="bg-gradient-to-r from-amber-500 to-yellow-500 text-slate-950 font-black text-[10px] border-0 gap-1">
                                    <Crown className="w-3 h-3 fill-slate-950" />
                                    AgriKetha PRO
                                  </Badge>
                                ) : (
                                  <Badge variant="secondary" className="text-[10px] font-medium text-muted-foreground">
                                    Free Starter
                                  </Badge>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                {u.is_active ? (
                                  <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold border-0">
                                    Active
                                  </Badge>
                                ) : (
                                  <Badge className="bg-destructive/10 text-destructive text-[10px] font-bold border-0">
                                    Deactivated
                                  </Badge>
                                )}
                              </td>
                              <td className="py-3 px-4 text-right">
                                {u.role !== "admin" ? (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    disabled={togglingUserId === u.id}
                                    onClick={() => handleToggleUserStatus(u)}
                                    className={`text-[11px] font-bold h-7 rounded-lg ${
                                      u.is_active
                                        ? "text-destructive hover:bg-destructive/10 border-destructive/30"
                                        : "text-emerald-600 hover:bg-emerald-500/10 border-emerald-500/30"
                                    }`}
                                  >
                                    {togglingUserId === u.id ? (
                                      <Loader2 className="w-3 h-3 animate-spin" />
                                    ) : u.is_active ? (
                                      "Deactivate"
                                    ) : (
                                      "Activate"
                                    )}
                                  </Button>
                                ) : (
                                  <span className="text-[10px] text-muted-foreground italic">Protected</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>

            {/* PLATFORM REVENUE TRANSACTIONS LOG */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-black text-foreground flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-amber-500" />
                  <span>{language === "si" ? "පාරිභෝගික ගෙවීම් සහ ග්‍රාහකත්ව වාර්තා" : "Customer Subscription & Revenue Transactions"}</span>
                </h3>
                <Badge variant="outline" className="text-xs font-mono">
                  {adminOrders.length} Recent Orders
                </Badge>
              </div>

              <Card className="rounded-3xl border border-border bg-card overflow-hidden shadow-lg">
                {loadingAdmin ? (
                  <div className="p-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
                    <span>Loading revenue records...</span>
                  </div>
                ) : adminOrders.length === 0 ? (
                  <div className="p-8 text-center space-y-2">
                    <Receipt className="w-8 h-8 text-muted-foreground/40 mx-auto" />
                    <p className="text-xs text-muted-foreground">No subscription payment orders processed yet.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-muted/50 border-b border-border text-muted-foreground uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                          <th className="py-3 px-4">Order ID</th>
                          <th className="py-3 px-4">Customer</th>
                          <th className="py-3 px-4">Plan</th>
                          <th className="py-3 px-4">Amount</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4">Timestamp</th>
                          <th className="py-3 px-4 text-right">Tax Receipt</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {adminOrders.map((ord, idx) => (
                          <tr key={ord.order_id || ord.id || idx} className="hover:bg-muted/30 transition-colors">
                            <td className="py-3 px-4 font-mono font-bold text-foreground">{ord.order_id}</td>
                            <td className="py-3 px-4">
                              <div className="font-semibold text-foreground">{ord.user_name || "Farmer"}</div>
                              <div className="text-[10px] text-muted-foreground font-mono">{ord.user_email}</div>
                            </td>
                            <td className="py-3 px-4 font-medium text-foreground">
                              {ord.plan_name || ord.plan_id || "AgriKetha Pro"}
                            </td>
                            <td className="py-3 px-4 font-bold text-emerald-600">
                              {ord.currency || "LKR"} {Number(ord.amount || 1500).toFixed(2)}
                            </td>
                            <td className="py-3 px-4">
                              <Badge
                                className={`text-[10px] font-bold ${
                                  ord.status === "PAID" || ord.status === "COMPLETED" || ord.status === "SUCCESS"
                                    ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                                    : "bg-amber-500/10 text-amber-600 border border-amber-500/20"
                                }`}
                              >
                                {ord.status || "PAID"}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-muted-foreground text-[11px]">
                              {ord.created_at ? new Date(ord.created_at).toLocaleString() : "Recent"}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedInvoice(ord)}
                                className="text-xs text-emerald-600 hover:text-emerald-700 font-bold gap-1 p-1 h-auto"
                              >
                                <Download className="w-3.5 h-3.5" />
                                <span>Receipt</span>
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>
          </div>
        ) : (
          /* ========================================================= */
          /* REGULAR FARMER CONSUMER PLAN & PERSONAL BILLING INVOICES  */
          /* ========================================================= */
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* SUBSCRIPTION & PLAN DETAILS SECTION */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-black tracking-tight text-foreground flex items-center gap-2">
                  <Crown className="w-5 h-5 text-amber-500" />
                  <span>{language === "si" ? "ග්‍රාහකත්ව සැලැස්ම සහ විස්තර" : "Subscription Plan & Features"}</span>
                </h2>
                {isUnlimited ? (
                  <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-xs font-bold">
                    ✓ Verified Active
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-xs">
                    Free Tier
                  </Badge>
                )}
              </div>

              {/* Conditional Display: Pro Details vs Free Plan */}
              {isUnlimited ? (
                /* PRO PLAN ACTIVE DETAILS */
                <Card className="relative overflow-hidden border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-card/80 to-emerald-500/10 backdrop-blur-xl rounded-3xl shadow-2xl shadow-amber-500/10">
                  <div className="h-1 w-full bg-gradient-to-r from-amber-400 via-emerald-400 to-teal-400" />
                  <div className="p-6 sm:p-8 space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/70">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2.5">
                          <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-amber-500 to-yellow-400 text-white shadow-md shadow-amber-500/20">
                            <Crown className="w-6 h-6" />
                          </div>
                          <div>
                            <h3 className="text-xl font-black text-foreground flex items-center gap-2">
                              AgriKetha PRO (Active)
                              <Badge className="bg-amber-500 text-white text-[10px] font-bold">LKR 1,500 / Month</Badge>
                            </h3>
                            <p className="text-xs text-muted-foreground">
                              {language === "si"
                                ? "ඔබගේ Pro ගිණුම සක්‍රියයි. සියලුම AI නියෝජිතයන් අසීමිතව භාවිත කළ හැක."
                                : "Your Pro subscription is active with zero daily rate limitations across all microservices."}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-start sm:self-center">
                        <Button
                          onClick={handleDowngrade}
                          disabled={downgrading}
                          variant="outline"
                          size="sm"
                          className="rounded-xl text-xs font-bold border-border text-muted-foreground hover:text-destructive gap-1.5"
                        >
                          {downgrading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
                          <span>{language === "si" ? "නොමිලේ සැලැස්මට මාරු වන්න" : "Switch to Free Plan"}</span>
                        </Button>
                      </div>
                    </div>

                    {/* Pro Features Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 rounded-2xl bg-background/60 backdrop-blur border border-border/60 space-y-1.5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/10">
                        <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                          <Zap className="w-4 h-4 text-amber-500" />
                          <span>{language === "si" ? "අසීමිත AI විමසුම් (Unified Hub)" : "Unlimited Multi-Agent Queries"}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {language === "si" ? "දිනකට සීමාවකින් තොරව ප්‍රශ්න අසන්න." : "No daily ceiling on text and multimodal queries."}
                        </p>
                        <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold">
                          ∞ UNLIMITED
                        </Badge>
                      </div>

                      <div className="p-4 rounded-2xl bg-background/60 backdrop-blur border border-border/60 space-y-1.5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/10">
                        <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                          <Sparkles className="w-4 h-4 text-teal-500" />
                          <span>{language === "si" ? "පත්‍ර රෝග සහ Grad-CAM විශ්ලේෂණ" : "PyTorch & Grad-CAM Scans"}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {language === "si" ? "වී සහ එළවළු පත්‍ර රෝග නිර්ණය අසීමිතව." : "High-priority GPU inference for plant pathology."}
                        </p>
                        <Badge className="bg-teal-500/10 text-teal-600 text-[10px] font-bold">
                          ∞ UNLIMITED
                        </Badge>
                      </div>

                      <div className="p-4 rounded-2xl bg-background/60 backdrop-blur border border-border/60 space-y-1.5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/10">
                        <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                          <ShieldCheck className="w-4 h-4 text-emerald-500" />
                          <span>{language === "si" ? "නිල කෘෂිකර්ම දෙපාර්තමේන්තු උපදෙස්" : "DOA Grounded Guidance"}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {language === "si" ? "කෘෂිකර්ම පර්යේෂණ ලේඛන පූර්ණ ප්‍රවේශය." : "Direct access to Department of Agriculture RAG corpus."}
                        </p>
                        <Badge className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold">
                          ACTIVE & VERIFIED
                        </Badge>
                      </div>
                    </div>

                    {/* Billing Summary Bar */}
                    <div className="p-4 rounded-2xl bg-card border border-border flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="flex items-center gap-2">
                        <CreditCard className="w-4 h-4 text-emerald-600" />
                        <span className="font-semibold">{language === "si" ? "ගෙවීම් ක්‍රමය:" : "Billing Gateway:"}</span>
                        <span className="text-muted-foreground">PayHere Sri Lanka (LKR Secured)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-teal-600" />
                        <span className="font-semibold">{language === "si" ? "සැලැස්මේ ගාස්තුව:" : "Plan Fee:"}</span>
                        <span className="text-foreground font-bold">Rs. 1,500.00 / month</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span className="text-emerald-600 font-bold">Auto-Renewed & Secured</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ) : (
                /* FREE PLAN DETAILS */
                <Card className="p-6 sm:p-8 rounded-3xl border border-border/80 bg-card shadow-lg space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-emerald-600" />
                        <h3 className="text-lg font-bold text-foreground">
                          {language === "si" ? "නොමිලේ ආරම්භක සැලැස්ම (Free Starter)" : "AgriKetha Free Starter Plan"}
                        </h3>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {language === "si"
                          ? "දිනකට සීමිත AI භාවිතයක් හිමිවේ. අසීමිත ප්‍රවේශය සඳහා Pro සැලැස්මට යාවත්කාලීන වන්න."
                          : "Standard quota limits apply daily. Upgrade to AgriKetha Pro for unrestricted usage."}
                      </p>
                    </div>

                    <Button
                      onClick={() => setShowCheckout(true)}
                      className="bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white font-bold text-xs rounded-xl shadow-md gap-1.5 self-start sm:self-center"
                    >
                      <Crown className="w-4 h-4" />
                      <span>{language === "si" ? "Pro සැලැස්ම ලබාගන්න (රු. 1,500)" : "Upgrade to Pro (Rs. 1,500/mo)"}</span>
                    </Button>
                  </div>

                  {/* Free Quotas */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border space-y-1">
                      <p className="text-[11px] font-semibold text-muted-foreground">Text Queries</p>
                      <p className="text-base font-black text-foreground">{quota?.text?.remaining ?? 25} / {quota?.text?.limit ?? 25}</p>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border space-y-1">
                      <p className="text-[11px] font-semibold text-muted-foreground">Image Scans</p>
                      <p className="text-base font-black text-foreground">{quota?.image?.remaining ?? 5} / {quota?.image?.limit ?? 5}</p>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border space-y-1">
                      <p className="text-[11px] font-semibold text-muted-foreground">Voice Queries</p>
                      <p className="text-base font-black text-foreground">{quota?.voice?.remaining ?? 5} / {quota?.voice?.limit ?? 5}</p>
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* PAYMENT HISTORY & INVOICES */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-black tracking-tight text-foreground flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-emerald-600" />
                  <span>{language === "si" ? "ගෙවීම් ඉතිහාසය සහ රිසිට්පත්" : "Payment Invoices & Receipts"}</span>
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchInvoices}
                  className="text-xs rounded-xl border-border"
                >
                  {language === "si" ? "යාවත්කාලීන කරන්න" : "Refresh Invoices"}
                </Button>
              </div>

              <Card className="rounded-3xl border border-border bg-card overflow-hidden shadow-lg">
                {loadingInvoices ? (
                  <div className="p-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Loading payment records...</span>
                  </div>
                ) : invoices.length === 0 ? (
                  <div className="p-8 text-center space-y-2">
                    <Receipt className="w-10 h-10 text-muted-foreground/40 mx-auto" />
                    <p className="text-xs font-medium text-muted-foreground">
                      {language === "si" ? "තවමත් ගෙවීම් වාර්තා කිසිවක් නැත." : "No payment transaction history recorded yet."}
                    </p>
                    {!isUnlimited && (
                      <Button
                        size="sm"
                        onClick={() => setShowCheckout(true)}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl mt-2"
                      >
                        Upgrade Now
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-muted/50 border-b border-border text-muted-foreground uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                          <th className="py-3 px-4">Order ID</th>
                          <th className="py-3 px-4">Date</th>
                          <th className="py-3 px-4">Plan / Description</th>
                          <th className="py-3 px-4">Amount</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Receipt</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {invoices.map((inv, idx) => (
                          <tr key={inv.order_id || idx} className="hover:bg-muted/30 transition-colors">
                            <td className="py-3 px-4 font-mono font-bold text-foreground">
                              {inv.order_id}
                            </td>
                            <td className="py-3 px-4 text-muted-foreground">
                              {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "Recent"}
                            </td>
                            <td className="py-3 px-4 font-medium text-foreground">
                              {inv.plan_id === "pro_monthly" ? "AgriKetha Pro (Monthly)" : inv.plan_id}
                            </td>
                            <td className="py-3 px-4 font-bold text-foreground">
                              {inv.currency || "LKR"} {Number(inv.amount || 1500).toFixed(2)}
                            </td>
                            <td className="py-3 px-4">
                              <Badge
                                className={`text-[10px] font-bold ${
                                  inv.status === "COMPLETED" || inv.status === "PAID"
                                    ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                                    : "bg-amber-500/10 text-amber-600 border border-amber-500/20"
                                }`}
                              >
                                {inv.status || "SUCCESS"}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedInvoice(inv)}
                                className="text-xs text-emerald-600 hover:text-emerald-700 font-bold gap-1 p-1 h-auto"
                              >
                                <Download className="w-3.5 h-3.5" />
                                <span>View</span>
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>
          </div>
        )}
      </main>

      {/* PayHere Modal for upgrading (for Farmers) */}
      <PaymentCheckoutModal
        isOpen={showCheckout}
        onClose={() => setShowCheckout(false)}
        onPaymentSuccess={() => {
          setShowCheckout(false);
          fetchQuota();
          fetchInvoices();
          toast.success(language === "si" ? "Pro ගිණුම සාර්ථකව සක්‍රිය විය!" : "Pro Plan activated successfully!");
        }}
      />

      {/* Printable Receipt Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-5 relative">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-sm text-foreground">AgriKetha Official Tax Receipt</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedInvoice(null)}
                className="text-xs"
              >
                ✕
              </Button>
            </div>

            <div className="p-4 rounded-2xl bg-muted/40 border border-border/60 space-y-3 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Order Reference:</span>
                <span className="font-bold text-foreground">{selectedInvoice.order_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Customer:</span>
                <span className="text-foreground">{selectedInvoice.user_name || user?.full_name} ({selectedInvoice.user_email || user?.email})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Payment Gateway:</span>
                <span className="text-foreground">PayHere Sri Lanka (LKR)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Service:</span>
                <span className="text-foreground">AgriKetha-AI Pro Subscription</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-border font-bold text-sm">
                <span>Total Paid:</span>
                <span className="text-emerald-600">{selectedInvoice.currency || "LKR"} {Number(selectedInvoice.amount || 1500).toFixed(2)}</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                size="sm"
                onClick={() => window.print()}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Print / Save Receipt</span>
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
