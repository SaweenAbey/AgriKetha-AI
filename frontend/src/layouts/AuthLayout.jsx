import React from "react";
import { Link } from "react-router-dom";
import { 
  Sprout, 
  ShieldCheck, 
  Sparkles, 
  TrendingUp, 
  Leaf, 
  Bot, 
  CheckCircle2, 
  Languages 
} from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

export const AuthLayout = ({ children, title, subtitle }) => {
  const { language, toggleLanguage, t } = useLanguage();
  return (
    <div className="min-h-screen w-full flex bg-gradient-to-br from-emerald-50/70 via-background to-teal-50/40 dark:from-slate-950 dark:via-emerald-950/20 dark:to-slate-950 text-foreground overflow-hidden">
      {/* Decorative ambient gradients */}
      <div className="fixed top-0 left-0 -translate-x-1/3 -translate-y-1/3 w-[500px] h-[500px] bg-emerald-400/15 dark:bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-0 right-0 translate-x-1/3 translate-y-1/3 w-[600px] h-[600px] bg-teal-400/15 dark:bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Left side: AgriKetha AI Brand & Feature Showcase (Visible on lg screens) */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden border-r border-emerald-100/60 dark:border-emerald-900/30 bg-gradient-to-b from-emerald-900 via-emerald-950 to-teal-950 text-white">
        {/* Background texture & glowing rings */}
        <div className="absolute inset-0 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:24px_24px] opacity-15" />
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-emerald-500/20 rounded-full blur-2xl" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-teal-500/20 rounded-full blur-2xl" />

        {/* Top Header / Brand Logo */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-3 group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-400 to-teal-300 p-0.5 shadow-lg shadow-emerald-500/30 transition-transform duration-300 group-hover:scale-105">
              <div className="w-full h-full bg-emerald-950 rounded-[14px] flex items-center justify-center">
                <Sprout className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-200 via-teal-100 to-white">
                  {t("appTitle")}
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  SL v1.0
                </span>
              </div>
              <p className="text-xs text-emerald-200/70 font-medium">
                {t("appSubtitle")}
              </p>
            </div>
          </Link>
        </div>

        {/* Middle Feature Highlights */}
        <div className="relative z-10 my-auto py-8 space-y-8 max-w-lg">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 text-xs font-semibold backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              Multi-Agent Agricultural Intelligence
            </div>
            <h1 className="text-3xl xl:text-4xl font-extrabold leading-tight text-white">
              {language === "si" ? "ස්වාධීන AI නියෝජිතයින් සමඟින් ශ්‍රී ලාංකීය ගොවිතැන බලගන්වමු" : "Empowering Sri Lankan Farming with Autonomous AI Agents"}
            </h1>
            <p className="text-sm xl:text-base text-emerald-100/80 leading-relaxed">
              {language === "si" ? "තත්‍ය කාලීන පත්‍ර රෝග විනිශ්චය, දිස්ත්‍රික් තොග මිල ගණන් සහ අපගේ පසට හා දේශගුණයට ගැළපෙන නිල කෘෂි උපදෙස්." : "Real-time crop disease diagnosis, regional market prices, and localized advice tailored for our soil and climate."}
            </p>
          </div>

          {/* Interactive Feature Cards */}
          <div className="grid grid-cols-1 gap-3.5">
            <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-200 hover:bg-white/10 hover:border-emerald-400/40">
              <div className="p-2.5 rounded-lg bg-emerald-500/20 text-emerald-300">
                <Leaf className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-emerald-100">{t("visionTitle")}</h4>
                <p className="text-xs text-emerald-200/70">{t("visionDesc")}</p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-200 hover:bg-white/10 hover:border-emerald-400/40">
              <div className="p-2.5 rounded-lg bg-teal-500/20 text-teal-300">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-emerald-100">{t("marketTitle")}</h4>
                <p className="text-xs text-emerald-200/70">{t("marketDesc")}</p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-200 hover:bg-white/10 hover:border-emerald-400/40">
              <div className="p-2.5 rounded-lg bg-amber-500/20 text-amber-300">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-emerald-100">{t("agent1Title")}</h4>
                <p className="text-xs text-emerald-200/70">{t("agent1Desc")}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Trust & Security Footer */}
        <div className="relative z-10 pt-6 border-t border-emerald-800/40 flex items-center justify-between text-xs text-emerald-300/70">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Secure Role-Based MongoDB & JWT Auth</span>
          </div>
          <div className="flex items-center gap-1 text-emerald-200">
            <Languages className="w-4 h-4" />
            <span>සිංහල | English</span>
          </div>
        </div>
      </div>

      {/* Right side: Form Area */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-6 sm:p-10 lg:p-12 overflow-y-auto">
        <div className="w-full max-w-md space-y-6">
          {/* Top Switcher Bar */}
          <div className="flex items-center justify-between">
            <div className="lg:hidden flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-600/30">
                <Sprout className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xl font-bold tracking-tight text-foreground">
                  {t("appTitle")}
                </span>
                <p className="text-[10px] text-muted-foreground">{t("appSubtitle")}</p>
              </div>
            </div>

            <div className="ml-auto">
              <button
                type="button"
                onClick={toggleLanguage}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-xs font-semibold shadow-sm transition-all"
                title="Change language / භාෂාව වෙනස් කරන්න"
              >
                <Languages className="w-3.5 h-3.5" />
                <span>{t("langSwitch")}</span>
              </button>
            </div>
          </div>

          {/* Form Content */}
          <div className="glass-card rounded-2xl p-6 sm:p-8 shadow-2xl border border-emerald-100 dark:border-emerald-900/40">
            {title && (
              <div className="text-center mb-6 space-y-1">
                <h2 className="text-2xl font-bold tracking-tight text-foreground">{title}</h2>
                {subtitle && <p className="text-xs sm:text-sm text-muted-foreground">{subtitle}</p>}
              </div>
            )}
            {children}
          </div>

          {/* Footer note */}
          <div className="text-center text-xs text-muted-foreground">
            <p>© {new Date().getFullYear()} AgriKetha-AI Platform. Built for Sri Lankan Agriculture.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
