import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Loader2, 
  AlertCircle, 
  Sprout, 
  ShieldCheck, 
  UserCheck 
} from "lucide-react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login, loading, error, setError } = useAuth();
  const { t } = useLanguage();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: true,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    if (localError) setLocalError("");
    if (error) setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");

    if (!formData.email || !formData.password) {
      setLocalError("Please enter both email and password.");
      return;
    }

    const result = await login(formData.email, formData.password);
    if (result.success) {
      navigate("/dashboard");
    }
  };

  // Quick Demo Credentials Auto-Fill
  const handleQuickFill = (role) => {
    if (role === "farmer") {
      setFormData({
        email: "farmer@agriketha.lk",
        password: "password123",
        rememberMe: true,
      });
    } else {
      setFormData({
        email: "admin@agriketha.lk",
        password: "adminpassword123",
        rememberMe: true,
      });
    }
    setLocalError("");
    if (error) setError(null);
  };

  return (
    <AuthLayout
      title={t("loginTitle")}
      subtitle={t("loginSub")}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Error notification */}
        {(localError || error) && (
          <Alert variant="destructive" className="animate-fade-in">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{localError || error}</AlertDescription>
          </Alert>
        )}

        {/* Quick Demo Selector */}
        <div className="p-3 bg-emerald-50/70 dark:bg-emerald-950/30 rounded-xl border border-emerald-100 dark:border-emerald-900/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300 uppercase tracking-wider">
              {t("quickDemoFill")}
            </span>
            <span className="text-[10px] text-muted-foreground">{t("clickToTest")}</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickFill("farmer")}
              className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg bg-white dark:bg-emerald-900/40 border border-emerald-200 dark:border-emerald-800 hover:border-emerald-500 hover:text-emerald-600 transition-all text-foreground"
            >
              <Sprout className="w-3.5 h-3.5 text-emerald-600" />
              <span>{t("demoFarmer")}</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("admin")}
              className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg bg-white dark:bg-emerald-900/40 border border-emerald-200 dark:border-emerald-800 hover:border-emerald-500 hover:text-emerald-600 transition-all text-foreground"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>{t("demoOfficer")}</span>
            </button>
          </div>
        </div>

        {/* Email Address */}
        <div className="space-y-1.5">
          <Label htmlFor="email" required>
            {t("emailLabel")}
          </Label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="e.g. kamal.farmer@gmail.com"
            value={formData.email}
            onChange={handleChange}
            icon={<Mail className="w-4 h-4" />}
            required
          />
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" required>
              {t("passwordLabel")}
            </Label>
            <a
              href="#forgot-password"
              onClick={(e) => {
                e.preventDefault();
                alert("Please contact your district agricultural officer or admin to reset your password.");
              }}
              className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
            >
              Forgot Password?
            </a>
          </div>
          <div className="relative">
            <Input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              icon={<Lock className="w-4 h-4" />}
              className="pr-10"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Remember Me */}
        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              name="rememberMe"
              checked={formData.rememberMe}
              onChange={handleChange}
              className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-border accent-emerald-600"
            />
            <span className="text-xs text-muted-foreground">Keep me signed in</span>
          </label>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="gradient"
          size="lg"
          className="w-full mt-2 group"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Authenticating...
            </>
          ) : (
            <>
              {t("signInBtn")}
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </>
          )}
        </Button>

        {/* Sign up prompt */}
        <div className="text-center pt-3 border-t border-border/60">
          <p className="text-xs text-muted-foreground">
            {t("noAccount")}{" "}
            <Link
              to="/signup"
              className="font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
            >
              {t("registerNow")}
            </Link>
          </p>
        </div>
      </form>
    </AuthLayout>
  );
};
