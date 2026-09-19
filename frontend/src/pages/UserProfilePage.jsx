import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { useQuota } from "@/context/QuotaContext";
import { userService, paymentService } from "@/services/api";
import { PaymentCheckoutModal } from "@/components/PaymentCheckoutModal";

const SRI_LANKA_DISTRICTS = [
  "Anuradhapura", "Polonnaruwa", "Kurunegala", "Puttalam", "Kandy", 
  "Matale", "Nuwara Eliya", "Badulla", "Monaragala", "Ratnapura", 
  "Kegalle", "Ampara", "Batticaloa", "Trincomalee", "Galle", 
  "Matara", "Hambantota", "Colombo", "Gampaha", "Kalutara", 
  "Jaffna", "Kilinochchi", "Mannar", "Vavuniya", "Mullaitivu"
];

export const UserProfilePage = () => {
  const { user, setUser, logout } = useAuth();
  const { quota, isUnlimited, upgradePlan, fetchQuota } = useQuota();
  const { language, toggleLanguage, t } = useLanguage();
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    phone_number: user?.phone_number || "",
    district: user?.district || "Kurunegala",
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Billing history state
  const [invoices, setInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(true);
  const [showCheckout, setShowCheckout] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        phone_number: user.phone_number || "",
        district: user.district || "Kurunegala",
      });
    }
  }, [user]);

  const fetchInvoices = async () => {
    try {
      setLoadingInvoices(true);
      const data = await paymentService.getHistory();
      if (data?.history) {
        setInvoices(data.history);
      }
    } catch (err) {
      console.warn("Could not fetch invoices:", err);
    } finally {
      setLoadingInvoices(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setSaveSuccess(false);
    try {
      const updated = await userService.updateProfile(formData);
      setUser(updated);
      localStorage.setItem("agriketha_user", JSON.stringify(updated));
      setSaveSuccess(true);
      setIsEditing(false);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Profile update failed:", err);
      alert("Failed to update profile. Please try again.");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleDowngrade = async () => {
    if (!window.confirm(language === "si" ? "ඔබට නොමිලේ සැලැස්මට (Free Plan) මාරු වීමට අවශ්‍ය බව සහතිකද?" : "Are you sure you want to switch to the Free Starter Plan?")) {
      return;
    }
    setDowngrading(true);
    setStatusMessage("");
    const res = await upgradePlan("free");
    setDowngrading(false);
    if (res.success) {
      setStatusMessage(language === "si" ? "නොමිලේ සැලැස්මට මාරු විය." : "Switched to Free Plan.");
      fetchQuota();
      setTimeout(() => setStatusMessage(""), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50/50 via-background to-teal-50/30 dark:from-slate-950 dark:via-emerald-950/20 dark:to-slate-950 text-foreground pb-16">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
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
              className="gap-1.5 text-xs font-semibold border-emerald-500/40 text-emerald-700 dark:text-emerald-300 rounded-xl"
            >
              <Languages className="w-3.5 h-3.5 text-emerald-600" />
              <span>{language === "si" ? "English" : "සිංහල"}</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="gap-1.5 text-xs text-muted-foreground hover:text-destructive hover:border-destructive rounded-xl"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>{t("signOut")}</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 space-y-8">
        {/* Status notification banner */}
        {statusMessage && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-sm font-semibold flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-5 h-5" />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* User Identity Header Card */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-800 via-emerald-900 to-teal-900 text-white p-6 sm:p-8 shadow-xl">
          <div className="absolute right-0 bottom-0 translate-x-12 translate-y-12 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
          
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-tr from-amber-400 via-emerald-400 to-teal-300 p-0.5 shadow-lg shadow-black/20">
                <div className="w-full h-full bg-slate-900 rounded-[14px] flex items-center justify-center text-white text-2xl font-black">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "A"}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                    {user?.full_name || "AgriKetha Farmer"}
                  </h1>
                  {isUnlimited ? (
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
                  {user?.district || "Sri Lanka"} • {user?.role === "admin" ? "Officer / Administrator" : "Registered Farmer"}
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
            <Card className="relative overflow-hidden border-2 border-amber-500/40 bg-gradient-to-br from-amber-500/5 via-card to-emerald-500/5 rounded-3xl shadow-xl">
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
                  <div className="p-4 rounded-2xl bg-muted/40 border border-border/60 space-y-1.5">
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

                  <div className="p-4 rounded-2xl bg-muted/40 border border-border/60 space-y-1.5">
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

                  <div className="p-4 rounded-2xl bg-muted/40 border border-border/60 space-y-1.5">
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
      </main>

      {/* PayHere Modal for upgrading */}
      <PaymentCheckoutModal
        isOpen={showCheckout}
        onClose={() => setShowCheckout(false)}
        onPaymentSuccess={() => {
          setShowCheckout(false);
          fetchQuota();
          fetchInvoices();
          setStatusMessage(language === "si" ? "Pro ගිණුම සාර්ථකව සක්‍රිය විය!" : "Pro Plan activated successfully!");
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
                <span className="text-foreground">{user?.full_name} ({user?.email})</span>
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
