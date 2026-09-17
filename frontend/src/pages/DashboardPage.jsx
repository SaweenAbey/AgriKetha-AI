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
  Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { AgentQueryAssistant } from "@/components/AgentQueryAssistant";

export const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("agent1");
  const agentSectionRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const scrollToAgent = () => {
    setActiveTab("agent1");
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
                <span className="font-bold text-lg text-foreground">AgriKetha-AI</span>
                <Badge variant="secondary" className="text-[10px]">
                  {user?.role === "admin" ? "Officer / Admin" : "Farmer Portal"}
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground hidden sm:block">
                Sri Lanka Smart Agricultural Multi-Agent System
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm font-semibold text-foreground">{user?.full_name || "Guest Farmer"}</span>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <MapPin className="w-3 h-3 text-emerald-600" />
                {user?.district || "Sri Lanka"}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="gap-1.5 text-xs text-muted-foreground hover:text-destructive hover:border-destructive"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-800 via-emerald-900 to-teal-900 text-white p-6 sm:p-8 shadow-xl">
          <div className="absolute right-0 bottom-0 translate-x-12 translate-y-12 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-200 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              Agent 1 (Voice & Text NLP) Active
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Ayubowan, {user?.full_name || "Farmer"}!
            </h1>
            <p className="text-sm text-emerald-100/80 leading-relaxed">
              Welcome to your AgriKetha-AI control hub. Ask questions via voice or text to activate Agent 1 NLP diagnostics, fertilizer plans, and crop advisory.
            </p>
          </div>
        </div>

        {/* User Profile Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="glass-card">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">Account Email</p>
                <p className="text-sm font-semibold text-foreground truncate max-w-[180px]">
                  {user?.email || "user@agriketha.lk"}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400">
                <MapPin className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">Assigned District</p>
                <p className="text-sm font-semibold text-foreground">
                  {user?.district || "Not Specified"}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium">RBAC Security Role</p>
                <p className="text-sm font-semibold text-foreground capitalize">
                  {user?.role || "Farmer"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Feature Cards Grid */}
        <div>
          <h2 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-600" />
            AI Modules & Multi-Agent Services
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Smart Farming AI Advisor (Agent 1) */}
            <Card 
              onClick={scrollToAgent}
              className="group cursor-pointer border-emerald-500/40 bg-emerald-500/5 hover:border-emerald-500 hover:shadow-xl transition-all duration-300 relative overflow-hidden"
            >
              <div className="absolute top-2 right-2">
                <Badge className="bg-emerald-600 text-white text-[10px] gap-1">
                  <Mic className="w-2.5 h-2.5" /> Voice Ready
                </Badge>
              </div>
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <Bot className="w-6 h-6" />
                </div>
                <CardTitle className="text-lg flex items-center justify-between">
                  Agent 1: Smart AI Advisor
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-emerald-600 transition-colors" />
                </CardTitle>
                <CardDescription>
                  Ask farming queries by voice or text. Real-time NLP entity and symptom extraction.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
                  Voice & Text Enabled
                </Badge>
              </CardContent>
            </Card>

            {/* Disease Detector */}
            <Card className="group hover:border-emerald-500/40 hover:shadow-xl transition-all duration-300">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-teal-100 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <Leaf className="w-6 h-6" />
                </div>
                <CardTitle className="text-lg flex items-center justify-between">
                  Crop Disease Diagnostics
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-teal-600 transition-colors" />
                </CardTitle>
                <CardDescription>
                  Upload or snap a leaf photo for instant computer vision pathology and Sinhala/Tamil recommendations.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-normal">
                  Vision Agent
                </Badge>
              </CardContent>
            </Card>

            {/* Market Prices */}
            <Card className="group hover:border-emerald-500/40 hover:shadow-xl transition-all duration-300">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <CardTitle className="text-lg flex items-center justify-between">
                  Market Price Advisory
                  <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-amber-600 transition-colors" />
                </CardTitle>
                <CardDescription>
                  Real-time market price feeds across Dambulla, Meegoda, and Manning Dedicated Economic Centers.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary" className="text-xs font-normal">
                  Live Price Feeds
                </Badge>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Dedicated Agent 1 Workspace Section */}
        <section ref={agentSectionRef} className="pt-2">
          <AgentQueryAssistant />
        </section>
      </main>
    </div>
  );
};

