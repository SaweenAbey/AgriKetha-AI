import React, { useState } from "react";
import {
  Sparkles,
  Crown,
  MessageSquare,
  Image as ImageIcon,
  Mic,
  Zap,
  CheckCircle2,
  X,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  RotateCcw,
  Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuota } from "@/context/QuotaContext";
import { useLanguage } from "@/context/LanguageContext";

export const QuotaWidget = ({ compact = false }) => {
  const { quota, isUnlimited, upgradePlan, showUpgradeModal, setShowUpgradeModal, loading } = useQuota();
  const { t, language } = useLanguage();
  const [upgrading, setUpgrading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  const textUsed = quota?.text?.used ?? 0;
  const textLimit = quota?.text?.limit ?? 25;
  const textRemaining = quota?.text?.remaining ?? 25;

  const imageUsed = quota?.image?.used ?? 0;
  const imageLimit = quota?.image?.limit ?? 5;
  const imageRemaining = quota?.image?.remaining ?? 5;

  const voiceUsed = quota?.voice?.used ?? 0;
  const voiceLimit = quota?.voice?.limit ?? 5;
  const voiceRemaining = quota?.voice?.remaining ?? 5;

  const getPercentage = (used, limit) => {
    if (isUnlimited || !limit) return 0;
    return Math.min(100, Math.round((used / limit) * 100));
  };

  const getBarColor = (pct) => {
    if (pct >= 90) return "bg-red-500";
    if (pct >= 60) return "bg-amber-500";
    return "bg-emerald-500";
  };

  const handlePlanToggle = async (targetPlan) => {
    setUpgrading(true);
    setStatusMsg("");
    const res = await upgradePlan(targetPlan);
    setUpgrading(false);
    if (res.success) {
      setStatusMsg(targetPlan === "premium" ? (language === "si" ? "Pro ගිණුම සාර්ථකව සක්‍රිය විය!" : "Pro Plan activated successfully!") : (language === "si" ? "නොමිලේ ගිණුමට මාරු විය." : "Switched to Free Plan."));
      setTimeout(() => {
        setShowUpgradeModal(false);
        setStatusMsg("");
      }, 1200);
    }
  };

  return (
    <>
      {/* Quota Strip / Widget */}
      <div className="p-3.5 sm:p-4 rounded-2xl bg-card border border-border/70 shadow-sm transition-all hover:border-emerald-500/30">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Plan Header */}
          <div className="flex items-center gap-2.5">
            <div
              className={`p-2 rounded-xl flex items-center justify-center ${
                isUnlimited
                  ? "bg-gradient-to-tr from-amber-500/20 to-yellow-500/30 text-amber-500 border border-amber-500/30 shadow-sm shadow-amber-500/10"
                  : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
              }`}
            >
              {isUnlimited ? <Crown className="w-4 h-4 animate-bounce" /> : <Zap className="w-4 h-4" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-black uppercase tracking-wider text-foreground">
                  {isUnlimited ? t("planPro") : t("planFree")}
                </span>
                <Badge
                  variant={isUnlimited ? "default" : "outline"}
                  className={`text-[10px] px-2 py-0.5 ${
                    isUnlimited
                      ? "bg-gradient-to-r from-amber-500 to-yellow-500 text-white font-bold border-0 shadow-sm"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {isUnlimited ? "👑 UNLIMITED" : "25 TEXT • 5 IMG • 5 VOICE"}
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">{t("dailyReset")}</p>
            </div>
          </div>

          {/* Counters Grid */}
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            {/* Text Quota */}
            <div className="p-2 sm:px-3 sm:py-2 rounded-xl bg-muted/40 border border-border/50">
              <div className="flex items-center justify-between gap-1 text-[11px] font-semibold text-muted-foreground mb-1">
                <span className="flex items-center gap-1">
                  <MessageSquare className="w-3 h-3 text-emerald-500" />
                  <span className="hidden sm:inline">{t("textQueries")}</span>
                  <span className="sm:hidden">Text</span>
                </span>
                <span className="text-foreground font-bold">
                  {isUnlimited ? "∞" : `${textRemaining}/${textLimit}`}
                </span>
              </div>
              {!isUnlimited && (
                <div className="w-full bg-muted h-1 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(getPercentage(textUsed, textLimit))}`}
                    style={{ width: `${getPercentage(textUsed, textLimit)}%` }}
                  />
                </div>
              )}
            </div>

            {/* Image Quota */}
            <div className="p-2 sm:px-3 sm:py-2 rounded-xl bg-muted/40 border border-border/50">
              <div className="flex items-center justify-between gap-1 text-[11px] font-semibold text-muted-foreground mb-1">
                <span className="flex items-center gap-1">
                  <ImageIcon className="w-3 h-3 text-teal-500" />
                  <span className="hidden sm:inline">{t("imageScans")}</span>
                  <span className="sm:hidden">Images</span>
                </span>
                <span className="text-foreground font-bold">
                  {isUnlimited ? "∞" : `${imageRemaining}/${imageLimit}`}
                </span>
              </div>
              {!isUnlimited && (
                <div className="w-full bg-muted h-1 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(getPercentage(imageUsed, imageLimit))}`}
                    style={{ width: `${getPercentage(imageUsed, imageLimit)}%` }}
                  />
                </div>
              )}
            </div>

            {/* Voice Quota */}
            <div className="p-2 sm:px-3 sm:py-2 rounded-xl bg-muted/40 border border-border/50">
              <div className="flex items-center justify-between gap-1 text-[11px] font-semibold text-muted-foreground mb-1">
                <span className="flex items-center gap-1">
                  <Mic className="w-3 h-3 text-amber-500" />
                  <span className="hidden sm:inline">{t("voiceQueries")}</span>
                  <span className="sm:hidden">Voice</span>
                </span>
                <span className="text-foreground font-bold">
                  {isUnlimited ? "∞" : `${voiceRemaining}/${voiceLimit}`}
                </span>
              </div>
              {!isUnlimited && (
                <div className="w-full bg-muted h-1 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getBarColor(getPercentage(voiceUsed, voiceLimit))}`}
                    style={{ width: `${getPercentage(voiceUsed, voiceLimit)}%` }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Action Upgrade / Switch Button */}
          <div className="flex items-center gap-2 self-end md:self-center">
            <Button
              type="button"
              size="sm"
              onClick={() => setShowUpgradeModal(true)}
              className={`rounded-xl text-xs font-bold gap-1.5 shadow-sm ${
                isUnlimited
                  ? "bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                  : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isUnlimited ? t("planPro") : t("upgradeToPro")}</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Modern Glassmorphic Upgrade Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-card border border-emerald-500/30 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-5 relative overflow-hidden">
            {/* Ambient glowing gradient */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-amber-500/20 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />

            {/* Close Button */}
            <button
              onClick={() => setShowUpgradeModal(false)}
              className="absolute right-4 top-4 p-1.5 rounded-full bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Modal Header */}
            <div className="text-center space-y-2 pt-2">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-yellow-400 text-white flex items-center justify-center mx-auto shadow-lg shadow-amber-500/20">
                <Crown className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-black tracking-tight text-foreground">
                {t("proBenefitsTitle")}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {language === "si"
                  ? "දෛනික සීමාවන්ගෙන් තොරව අසීමිතව කෘෂිකාර්මික AI විශ්ලේෂණ ලබාගැනීමට Pro ගිණුම සක්‍රිය කරගන්න."
                  : "Enjoy unrestricted access to all 4 AI agents with zero daily limitations, high-speed priority inference, and deep analytics."}
              </p>
            </div>

            {/* Perks List */}
            <div className="space-y-2.5 p-4 rounded-2xl bg-muted/30 border border-border">
              <div className="flex items-center gap-2.5 text-xs text-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t("benefit1")}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t("benefit2")}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t("benefit3")}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs text-foreground font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t("benefit4")}</span>
              </div>
            </div>

            {/* Status notification */}
            {statusMsg && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-xs font-semibold text-center animate-in fade-in">
                {statusMsg}
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-2 pt-1">
              {!isUnlimited ? (
                <Button
                  onClick={() => handlePlanToggle("premium")}
                  disabled={upgrading}
                  className="w-full py-5 rounded-2xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white font-bold text-sm shadow-lg shadow-amber-500/20 gap-2"
                >
                  {upgrading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>{t("activateProBtn")}</span>
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  onClick={() => handlePlanToggle("free")}
                  disabled={upgrading}
                  variant="outline"
                  className="w-full py-5 rounded-2xl font-bold text-xs gap-2 border-border"
                >
                  {upgrading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>{t("switchToFreeBtn")}</span>
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
