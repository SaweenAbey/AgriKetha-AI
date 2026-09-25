import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Sprout, 
  Leaf, 
  TrendingUp, 
  Bot, 
  MapPin, 
  Mail, 
  LogOut, 
  ShieldCheck, 
  Sparkles, 
  Layers, 
  ArrowUpRight,
  Mic,
  Activity,
  Eye,
  Zap,
  BookOpen,
  Globe,
  Languages,
  Crown,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { useQuota } from "@/context/QuotaContext";
import { UnifiedOrchestratorAssistant } from "@/components/UnifiedOrchestratorAssistant";
import { AgentQueryAssistant } from "@/components/AgentQueryAssistant";
import { CropDiagnosticsAssistant } from "@/components/CropDiagnosticsAssistant";
import { MarketPriceAdvisor } from "@/components/MarketPriceAdvisor";

export const DashboardPage = () => {
  const { user, logout } = useAuth();
  const { isUnlimited } = useQuota();
  const { language, toggleLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("orchestrator"); // 'orchestrator', 'agent1', 'vision', 'market'
  const agentSectionRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleTabSwitch = (tab) => {
    setActiveTab(tab);
    if (agentSectionRef.current) {
      agentSectionRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50/50 via-background to-teal-50/30 dark:from-slate-950 dark:via-emerald-950/20 dark:to-slate-950 text-foreground pb-12">
      {/* Navigation Bar */}
      <header className="sticky top-0 z-30 border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-600/20">
              <Sprout className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-foreground">{t("appTitle")}</span>
                <Badge variant="secondary" className="text-[10px]">
                  {user?.role === "admin" ? t("officerAdmin") : t("farmerPortal")}
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground hidden sm:block">
                {t("appSubtitle")}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Language Switcher Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className="gap-1.5 text-xs font-semibold border-emerald-500/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 rounded-xl"
              title="Change Language / භාෂාව වෙනස් කරන්න"
            >
              <Languages className="w-3.5 h-3.5 text-emerald-600" />
              <span>{language === "si" ? "English" : "සිංහල"}</span>
            </Button>

            {/* Clickable User Profile & Plan Pill */}
            <button
              onClick={() => navigate("/profile")}
              className="group flex items-center gap-2.5 px-3 py-1.5 rounded-2xl bg-card border border-border/80 hover:border-emerald-500/50 hover:bg-muted/40 transition-all shadow-sm text-left cursor-pointer"
              title={language === "si" ? "පරිශීලක තොරතුරු සහ ගිණුම් විස්තර සඳහා ක්ලික් කරන්න" : "Click to view Profile & Subscription Details"}
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center font-bold text-xs shadow-sm group-hover:scale-105 transition-transform">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "A"}
              </div>
              <div className="hidden sm:flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-foreground group-hover:text-emerald-600 transition-colors">
                    {user?.full_name || t("guestFarmer")}
                  </span>
                  {isUnlimited ? (
                    <Badge className="bg-gradient-to-r from-amber-500 to-yellow-500 text-slate-950 font-black text-[9px] px-1.5 py-0 border-0 shadow-sm">
                      👑 PRO
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-[9px] px-1.5 py-0 text-muted-foreground border-border">
                      FREE
                    </Badge>
                  )}
                </div>
                <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                  <MapPin className="w-2.5 h-2.5 text-emerald-600" />
                  {user?.district || t("sriLanka")}
                </span>
              </div>
            </button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="gap-1.5 text-xs text-muted-foreground hover:text-destructive hover:border-destructive rounded-xl"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>{t("signOut")}</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-800 via-emerald-900 to-teal-900 text-white p-6 sm:p-8 shadow-xl">
          <div className="absolute right-0 bottom-0 translate-x-12 translate-y-12 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="max-w-2xl space-y-3">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-200 text-xs font-medium">
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                {t("welcomeTag")}
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                {t("ayubowan")}, {user?.full_name || t("farmer")}!
              </h1>
              <p className="text-sm text-emerald-100/80 leading-relaxed">
                {t("welcomeDesc")}
              </p>
            </div>

            <div className="self-start sm:self-center shrink-0">
              <Button
                onClick={() => navigate("/profile")}
                size="sm"
                className="bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-2xl text-xs font-bold gap-2 backdrop-blur-sm shadow-md py-5 px-4"
              >
                {isUnlimited ? (
                  <>
                    <Crown className="w-4 h-4 text-amber-300" />
                    <span>{language === "si" ? "Pro ගිණුම සහ විස්තර" : "Pro Profile & Billing"}</span>
                  </>
                ) : (
                  <>
                    <User className="w-4 h-4 text-emerald-300" />
                    <span>{language === "si" ? "පරිශීලක ගිණුම (Profile)" : "User Profile & Plan"}</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div>
          <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-600" />
            {t("aiModulesTitle")}
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Agent 4: Unified Multi-Agent Orchestrator */}
            <Card 
              onClick={() => handleTabSwitch("orchestrator")}
              className={`group cursor-pointer transition-all duration-300 relative overflow-hidden ${
                activeTab === "orchestrator"
                  ? "border-emerald-500 bg-emerald-500/10 shadow-lg ring-2 ring-emerald-500/20"
                  : "border-border hover:border-emerald-500/50 hover:shadow-xl"
              }`}
            >
              <div className="absolute top-2 right-2">
                <Badge className="bg-emerald-600 text-white text-[10px] gap-1 animate-pulse">
                  <Sparkles className="w-2.5 h-2.5" /> {t("agent4Badge")}
                </Badge>
              </div>
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <Zap className="w-6 h-6" />
                </div>
                <CardTitle className="text-base flex items-center justify-between">
                  {t("agent4Title")}
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-emerald-600 transition-colors" />
                </CardTitle>
                <CardDescription className="text-xs">
                  {t("agent4Desc")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
                  {t("agent4Sub")}
                </Badge>
              </CardContent>
            </Card>

            {/* Smart Farming AI Advisor (Agent 1/2) */}
            <Card 
              onClick={() => handleTabSwitch("agent1")}
              className={`group cursor-pointer transition-all duration-300 relative overflow-hidden ${
                activeTab === "agent1"
                  ? "border-emerald-500 bg-emerald-500/10 shadow-lg ring-2 ring-emerald-500/20"
                  : "border-border hover:border-emerald-500/50 hover:shadow-xl"
              }`}
            >
              <div className="absolute top-2 right-2">
                <Badge className="bg-emerald-600 text-white text-[10px] gap-1">
                  <Mic className="w-2.5 h-2.5" /> {t("agent1Badge")}
                </Badge>
              </div>
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <Bot className="w-6 h-6" />
                </div>
                <CardTitle className="text-base flex items-center justify-between">
                  {t("agent1Title")}
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-emerald-600 transition-colors" />
                </CardTitle>
                <CardDescription className="text-xs">
                  {t("agent1Desc")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
                  {t("agent1Sub")}
                </Badge>
              </CardContent>
            </Card>

            {/* Vision Agent: Disease Detector */}
            <Card 
              onClick={() => handleTabSwitch("vision")}
              className={`group cursor-pointer transition-all duration-300 relative overflow-hidden ${
                activeTab === "vision"
                  ? "border-teal-500 bg-teal-500/10 shadow-lg ring-2 ring-teal-500/20"
                  : "border-border hover:border-teal-500/50 hover:shadow-xl"
              }`}
            >
              <div className="absolute top-2 right-2">
                <Badge className="bg-teal-600 text-white text-[10px] gap-1">
                  <Eye className="w-2.5 h-2.5" /> {t("visionBadge")}
                </Badge>
              </div>
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-teal-100 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <Leaf className="w-6 h-6" />
                </div>
                <CardTitle className="text-base flex items-center justify-between">
                  {t("visionTitle")}
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-teal-600 transition-colors" />
                </CardTitle>
                <CardDescription className="text-xs">
                  {t("visionDesc")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-medium text-teal-700 dark:text-teal-300">
                  {t("visionSub")}
                </Badge>
              </CardContent>
            </Card>

            {/* Market Prices */}
            <Card 
              onClick={() => handleTabSwitch("market")}
              className={`group cursor-pointer transition-all duration-300 relative overflow-hidden ${
                activeTab === "market"
                  ? "border-amber-500 bg-amber-500/10 shadow-lg ring-2 ring-amber-500/20"
                  : "border-border hover:border-amber-500/50 hover:shadow-xl"
              }`}
            >
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <CardTitle className="text-base flex items-center justify-between">
                  {t("marketTitle")}
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-amber-600 transition-colors" />
                </CardTitle>
                <CardDescription className="text-xs">
                  {t("marketDesc")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-normal">
                  {t("marketSub")}
                </Badge>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Dedicated Agent Workspace Section */}
        <section ref={agentSectionRef} className="pt-2 space-y-4">
          {/* Workspace Tabs Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <Button
                variant={activeTab === "orchestrator" ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab("orchestrator")}
                className={`gap-2 rounded-xl text-xs font-bold ${
                  activeTab === "orchestrator" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""
                }`}
              >
                <Zap className="w-4 h-4" />
                {t("tabOrchestrator")}
              </Button>

              <Button
                variant={activeTab === "agent1" ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab("agent1")}
                className={`gap-2 rounded-xl text-xs font-bold ${
                  activeTab === "agent1" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""
                }`}
              >
                <Bot className="w-4 h-4" />
                {t("tabAgent1")}
              </Button>

              <Button
                variant={activeTab === "vision" ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab("vision")}
                className={`gap-2 rounded-xl text-xs font-bold ${
                  activeTab === "vision" ? "bg-teal-600 hover:bg-teal-700 text-white" : ""
                }`}
              >
                <Leaf className="w-4 h-4" />
                {t("tabVision")}
              </Button>

              <Button
                variant={activeTab === "market" ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab("market")}
                className={`gap-2 rounded-xl text-xs font-bold ${
                  activeTab === "market" ? "bg-amber-600 hover:bg-amber-700 text-white" : ""
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                {t("tabMarket")}
              </Button>
            </div>

            <Badge variant="secondary" className="text-xs">
              {t("activeModule")}:{" "}
              {activeTab === "orchestrator"
                ? t("tabOrchestrator")
                : activeTab === "agent1"
                ? t("tabAgent1")
                : activeTab === "vision"
                ? t("tabVision")
                : t("tabMarket")}
            </Badge>
          </div>

          {/* Active Module Body */}
          {activeTab === "orchestrator" && <UnifiedOrchestratorAssistant />}
          {activeTab === "agent1" && <AgentQueryAssistant />}
          {activeTab === "vision" && <CropDiagnosticsAssistant />}
          {activeTab === "market" && <MarketPriceAdvisor />}
        </section>
      </main>
    </div>

  );
};


