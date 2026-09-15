import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { 
  User, 
  Mail, 
  Phone, 
  Lock, 
  MapPin, 
  Sprout, 
  ShieldCheck, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Loader2, 
  AlertCircle, 
  CheckCircle2 
} from "lucide-react";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { SRI_LANKA_DISTRICTS } from "@/constants/sriLankaData";
import { useAuth } from "@/context/AuthContext";

export const SignupPage = () => {
  const navigate = useNavigate();
  const { register, login, loading, error, setError } = useAuth();

  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    district: "Anuradhapura",
    role: "farmer",
    password: "",
    confirmPassword: "",
    agreeTerms: true,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    if (localError) setLocalError("");
    if (error) setError(null);
  };

  // Basic password strength calculation
  const getPasswordStrength = (pwd) => {
    if (!pwd) return 0;
    let score = 0;
    if (pwd.length >= 6) score += 1;
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;
    return Math.min(score, 4);
  };

  const pwdScore = getPasswordStrength(formData.password);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    setSuccessMessage("");

    if (!formData.full_name.trim()) {
      setLocalError("Please provide your full name.");
      return;
    }

    if (!formData.email.trim()) {
      setLocalError("Please provide a valid email address.");
      return;
    }

    if (formData.password.length < 6) {
      setLocalError("Password must be at least 6 characters long.");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setLocalError("Passwords do not match.");
      return;
    }

    if (!formData.agreeTerms) {
      setLocalError("You must accept the terms of service to proceed.");
      return;
    }

    const payload = {
      full_name: formData.full_name.trim(),
      email: formData.email.trim().toLowerCase(),
      phone_number: formData.phone_number.trim() || undefined,
      district: formData.district,
      role: formData.role,
      password: formData.password,
    };

    const res = await register(payload);
    if (res.success) {
      setSuccessMessage("Account created successfully! Signing you in...");
      // Auto login
      const loginRes = await login(formData.email, formData.password);
      if (loginRes.success) {
        setTimeout(() => navigate("/dashboard"), 1200);
      } else {
        setTimeout(() => navigate("/login"), 1500);
      }
    }
  };

  return (
    <AuthLayout
      title="Create Your Account"
      subtitle="Join AgriKetha-AI to boost crop yield and optimize farm revenue"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Error notification */}
        {(localError || error) && (
          <Alert variant="destructive" className="animate-fade-in">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{localError || error}</AlertDescription>
          </Alert>
        )}

        {/* Success notification */}
        {successMessage && (
          <Alert variant="success" className="animate-fade-in">
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}

        {/* Role Selector Cards */}
        <div className="space-y-1.5">
          <Label required>Account Type / ගිණුම් වර්ගය</Label>
          <div className="grid grid-cols-2 gap-2.5">
            <button
              type="button"
              onClick={() => setFormData((p) => ({ ...p, role: "farmer" }))}
              className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all ${
                formData.role === "farmer"
                  ? "bg-emerald-50/90 dark:bg-emerald-950/50 border-emerald-500 ring-2 ring-emerald-500/20 shadow-sm"
                  : "bg-background border-border hover:border-emerald-200"
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <div className={`p-1.5 rounded-lg ${formData.role === "farmer" ? "bg-emerald-600 text-white" : "bg-muted text-muted-foreground"}`}>
                  <Sprout className="w-4 h-4" />
                </div>
                {formData.role === "farmer" && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                )}
              </div>
              <span className="text-xs font-bold text-foreground">Farmer</span>
              <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                Crop disease AI & market rates
              </span>
            </button>

            <button
              type="button"
              onClick={() => setFormData((p) => ({ ...p, role: "admin" }))}
              className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all ${
                formData.role === "admin"
                  ? "bg-emerald-50/90 dark:bg-emerald-950/50 border-emerald-500 ring-2 ring-emerald-500/20 shadow-sm"
                  : "bg-background border-border hover:border-emerald-200"
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <div className={`p-1.5 rounded-lg ${formData.role === "admin" ? "bg-emerald-600 text-white" : "bg-muted text-muted-foreground"}`}>
                  <ShieldCheck className="w-4 h-4" />
                </div>
                {formData.role === "admin" && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                )}
              </div>
              <span className="text-xs font-bold text-foreground">Officer / Admin</span>
              <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                Regional oversight & reports
              </span>
            </button>
          </div>
        </div>

        {/* Full Name */}
        <div className="space-y-1.5">
          <Label htmlFor="full_name" required>
            Full Name / සම්පූර්ණ නම
          </Label>
          <Input
            id="full_name"
            name="full_name"
            type="text"
            placeholder="e.g. Sunil Shantha"
            value={formData.full_name}
            onChange={handleChange}
            icon={<User className="w-4 h-4" />}
            required
          />
        </div>

        {/* Email Address */}
        <div className="space-y-1.5">
          <Label htmlFor="email" required>
            Email Address
          </Label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="e.g. sunil.agri@gmail.com"
            value={formData.email}
            onChange={handleChange}
            icon={<Mail className="w-4 h-4" />}
            required
          />
        </div>

        {/* Phone & District Two-column row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Phone Number */}
          <div className="space-y-1.5">
            <Label htmlFor="phone_number">Phone (දුරකථන)</Label>
            <Input
              id="phone_number"
              name="phone_number"
              type="tel"
              placeholder="07X XXX XXXX"
              value={formData.phone_number}
              onChange={handleChange}
              icon={<Phone className="w-4 h-4" />}
            />
          </div>

          {/* District Dropdown */}
          <div className="space-y-1.5">
            <Label htmlFor="district" required>District (දිස්ත්‍රික්කය)</Label>
            <div className="relative">
              <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
                <MapPin className="w-4 h-4" />
              </div>
              <select
                id="district"
                name="district"
                value={formData.district}
                onChange={handleChange}
                className="flex h-11 w-full rounded-xl border border-input bg-background/80 pl-11 pr-4 py-2 text-sm text-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:border-emerald-500 transition-all cursor-pointer"
              >
                {SRI_LANKA_DISTRICTS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Password & Confirm Password */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="password" required>
              Password
            </Label>
            <div className="relative">
              <Input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                placeholder="Min 6 characters"
                value={formData.password}
                onChange={handleChange}
                icon={<Lock className="w-4 h-4" />}
                className="pr-9"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="confirmPassword" required>
              Confirm Password
            </Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type={showPassword ? "text" : "password"}
              placeholder="Re-type password"
              value={formData.confirmPassword}
              onChange={handleChange}
              icon={<Lock className="w-4 h-4" />}
              required
            />
          </div>
        </div>

        {/* Password Strength Indicator */}
        {formData.password && (
          <div className="space-y-1">
            <div className="flex gap-1 h-1 w-full bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  pwdScore <= 1
                    ? "w-1/4 bg-red-500"
                    : pwdScore === 2
                    ? "w-2/4 bg-amber-500"
                    : pwdScore === 3
                    ? "w-3/4 bg-teal-500"
                    : "w-full bg-emerald-500"
                }`}
              />
            </div>
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>Security level</span>
              <span className="font-semibold">
                {pwdScore <= 1 ? "Weak" : pwdScore === 2 ? "Moderate" : pwdScore === 3 ? "Good" : "Strong"}
              </span>
            </div>
          </div>
        )}

        {/* Terms and Conditions */}
        <div className="pt-1">
          <label className="flex items-start gap-2.5 cursor-pointer select-none">
            <input
              type="checkbox"
              name="agreeTerms"
              checked={formData.agreeTerms}
              onChange={handleChange}
              className="mt-0.5 w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-border accent-emerald-600"
            />
            <span className="text-xs text-muted-foreground leading-snug">
              I agree to the{" "}
              <a href="#terms" className="text-emerald-600 dark:text-emerald-400 underline">
                Terms of Agricultural Data Usage
              </a>{" "}
              and Privacy Policy.
            </span>
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
              Creating AgriKetha Account...
            </>
          ) : (
            <>
              Register & Start Farming Smart
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </>
          )}
        </Button>

        {/* Sign In prompt */}
        <div className="text-center pt-3 border-t border-border/60">
          <p className="text-xs text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
            >
              Sign In here
            </Link>
          </p>
        </div>
      </form>
    </AuthLayout>
  );
};
