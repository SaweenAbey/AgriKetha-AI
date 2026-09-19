import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  Bot,
  Leaf,
  BookOpen,
  Send,
  Mic,
  MicOff,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Clock,
  Volume2,
  VolumeX,
  RotateCcw,
  Copy,
  Check,
  Upload,
  X,
  ShieldAlert,
  FileText,
  Activity,
  ChevronRight,
  ExternalLink,
  Layers,
  Award,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { orchestratorService } from "@/services/api";
import { useLanguage } from "@/context/LanguageContext";
import { useQuota } from "@/context/QuotaContext";
import { QuotaWidget } from "@/components/QuotaWidget";

const PRESET_QUESTIONS = [
  {
    crop: "Tomato (තක්කාලි)",
    icon: "🍅",
    text: "තක්කාලි කොළ වල කළු පාට ලප සහ කහ වීමක් තියෙනවා, මොකක්ද මේ රෝගය සහ ප්‍රතිකාරය?",
    category: "Pathology & Treatment",
  },
  {
    crop: "Paddy (වී / ගොයම්)",
    icon: "🌾",
    text: "ගොයම් කොළ කහ වෙලා කරටි වියළෙනවා, යෙදිය යුතු නිර්දේශිත පොහොර හෝ ප්‍රතිකාර මොනවාද?",
    category: "Paddy Health & Fertilizer",
  },
  {
    crop: "Chilli (මිරිස්)",
    icon: "🌶️",
    text: "මිරිස් කොළ හැකිලිලා සුදු මැස්සන් ඉන්නවා. පාලනය කරන්නේ කොහොමද?",
    category: "Pest & Leaf Curl",
  },
  {
    crop: "Potato (අල)",
    icon: "🥔",
    text: "My potato leaves have dark concentric rings and wilting. What should I do?",
    category: "Blight Diagnostic",
  },
];

export const UnifiedOrchestratorAssistant = () => {
  const { language, t } = useLanguage();
  const { updateQuotaFromResponse, fetchQuota, setShowUpgradeModal } = useQuota();
  const [question, setQuestion] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isQuotaError, setIsQuotaError] = useState(false);
  const [lastInputMode, setLastInputMode] = useState("text");
  const [history, setHistory] = useState([]);
  const [copied, setCopied] = useState(false);

  // Agent connectivity status
  const [agentStatuses, setAgentStatuses] = useState({
    orchestrator: "online",
    gemini_llm: "configured",
    query_agent: "checking",
    vision_agent: "checking",
    research_agent: "checking",
  });

  // Speech Recognition
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const recognitionRef = useRef(null);

  // Text to Speech
  const [isSpeaking, setIsSpeaking] = useState(false);
  const synthRef = useRef(window.speechSynthesis);

  // File input ref
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Check speech recognition support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
    } else {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = language === "si" ? "si-LK" : "en-US";
      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setQuestion((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setLastInputMode("voice");
        setIsListening(false);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }

    loadHistory();
    checkAgentStatuses();

    return () => {
      if (recognitionRef.current) recognitionRef.current.abort();
      if (synthRef.current) synthRef.current.cancel();
    };
  }, [language]);

  const checkAgentStatuses = async () => {
    try {
      const res = await orchestratorService.getOrchestratorStatus();
      if (res) setAgentStatuses(res);
    } catch {
      setAgentStatuses({
        orchestrator: "online",
        gemini_llm: "configured",
        query_agent: "fallback",
        vision_agent: "online",
        research_agent: "online",
      });
    }
  };

  const loadHistory = async () => {
    try {
      const res = await orchestratorService.getOrchestratorHistory(10);
      if (res && Array.isArray(res)) setHistory(res);
    } catch (err) {
      console.warn("History load notice:", err);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        setError(language === "si" ? "කරුණාකර නිවැරදි ඡායාරූප ගොනුවක් තෝරන්න (JPG, PNG, WEBP)." : "Please select a valid image file (JPG, PNG, WEBP).");
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const toggleVoiceListening = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setError(null);
      setIsQuotaError(false);
      try {
        recognitionRef.current.lang = language === "si" ? "si-LK" : "en-US";
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.warn("Recognition start error:", err);
      }
    }
  };

  const toggleTextToSpeech = (text) => {
    if (!synthRef.current) return;
    if (isSpeaking) {
      synthRef.current.cancel();
      setIsSpeaking(false);
      return;
    }

    const cleanText = text
      .replace(/[#*_`]/g, "")
      .replace(/\[.*?\]\(.*?\)/g, "")
      .slice(0, 1000);

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95;
    utterance.lang = language === "si" ? "si-LK" : "en-US";
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    synthRef.current.speak(utterance);
    setIsSpeaking(true);
  };

  const handleCopyAdvisory = () => {
    if (!result?.advisory) return;
    navigator.clipboard.writeText(result.advisory);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!question.trim()) {
      setError(language === "si" ? "කරුණාකර ඔබගේ වගා ගැටලුව ලියන්න හෝ හඬින් පවසන්න." : "Please enter or speak your farming question.");
      return;
    }

    setLoading(true);
    setError(null);
    setIsQuotaError(false);
    if (synthRef.current) synthRef.current.cancel();
    setIsSpeaking(false);

    try {
      const formData = new FormData();
      formData.append("question", question.trim());
      formData.append("language", language);
      formData.append("is_voice", lastInputMode === "voice" ? "true" : "false");
      formData.append("input_mode", lastInputMode);
      if (selectedFile) {
        formData.append("file", selectedFile);
      }

      const response = await orchestratorService.orchestrateQuery(formData);
      setResult(response);
      if (response.quota_status) {
        updateQuotaFromResponse(response.quota_status);
      }
      fetchQuota();
      loadHistory();
      setLastInputMode("text");
    } catch (err) {
      console.error("Orchestrator request failed:", err);
      const is429 = err.response?.status === 429;
      setIsQuotaError(is429);
      const serverDetail = err.response?.data?.detail;
      const msg = typeof serverDetail === "object" ? serverDetail.message : serverDetail;
      setError(
        msg ||
          (is429
            ? t("quotaExceededMsg")
            : language === "si"
            ? "බහු-නියෝජිත විශ්ලේෂණය සම්පූර්ණ කළ නොහැකි විය. කරුණාකර අන්තර්ජාල සබඳතාව පරීක්ෂා කරන්න."
            : "Could not complete the multi-agent analysis. Please verify your internet connection and backend services.")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Daily Usage Quota Widget */}
      <QuotaWidget />

      {/* Header Banner with Agent Architecture */}
      <Card className="border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-background to-teal-950/20 backdrop-blur-xl shadow-xl overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
                {t("orchestratorTag")}
              </div>
              <CardTitle className="text-2xl font-black text-foreground tracking-tight">
                {t("orchestratorHeading")}
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm text-muted-foreground">
                {t("orchestratorSub")}
              </CardDescription>
            </div>

            {/* Microservice Live Badges */}
            <div className="flex flex-wrap items-center gap-2">
              <Badge
                variant="outline"
                className={`text-[11px] gap-1 px-2.5 py-1 ${
                  agentStatuses.query_agent === "online"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                }`}
              >
                <Bot className="w-3 h-3" />
                Agent 2: NLP ({agentStatuses.query_agent})
              </Badge>

              <Badge
                variant="outline"
                className={`text-[11px] gap-1 px-2.5 py-1 ${
                  agentStatuses.vision_agent === "online"
                    ? "bg-teal-500/10 text-teal-400 border-teal-500/30"
                    : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                }`}
              >
                <Leaf className="w-3 h-3" />
                Agent 1: Vision (:8002)
              </Badge>

              <Badge
                variant="outline"
                className={`text-[11px] gap-1 px-2.5 py-1 ${
                  agentStatuses.research_agent === "online"
                    ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                    : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                }`}
              >
                <BookOpen className="w-3 h-3" />
                Agent 3: RAG (:8004)
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Main Input Workspace */}
      <Card className="glass-card shadow-lg border-border">
        <CardContent className="p-5 sm:p-6 space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                {t("step1Label")}
              </label>
              <div className="relative">
                <textarea
                  rows={3}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={t("textareaPlaceholder")}
                  className="w-full rounded-2xl bg-muted/30 border border-input px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 resize-none pr-12 transition-all placeholder:text-muted-foreground/60"
                />
                {voiceSupported && (
                  <button
                    type="button"
                    onClick={toggleVoiceListening}
                    className={`absolute right-3 top-3 p-2 rounded-xl transition-all ${
                      isListening
                        ? "bg-red-500 text-white animate-pulse"
                        : "bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-600 dark:text-emerald-400"
                    }`}
                    title={isListening ? t("listeningTitle") : t("voiceInputTitle")}
                  >
                    {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>
                )}
              </div>
            </div>

            {/* Quick Presets */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[11px] font-semibold text-muted-foreground">{t("quickPresets")}:</span>
              {PRESET_QUESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuestion(item.text)}
                  className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 transition-colors flex items-center gap-1"
                >
                  <span>{item.icon}</span>
                  <span className="truncate max-w-[200px]">{item.crop}</span>
                </button>
              ))}
            </div>

            {/* Image Upload Area (Optional) */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                {t("step2Label")}
              </label>

              {!previewUrl ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-border hover:border-emerald-500/60 rounded-2xl p-4 text-center cursor-pointer bg-muted/20 hover:bg-emerald-500/5 transition-all group"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <div className="flex flex-col items-center justify-center gap-2">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <ImageIcon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-foreground">{t("uploadTitle")}</p>
                      <p className="text-[11px] text-muted-foreground">{t("uploadSub")}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-4 p-3 rounded-2xl bg-muted/40 border border-border">
                  <img
                    src={previewUrl}
                    alt="Selected leaf"
                    className="w-16 h-16 object-cover rounded-xl border border-border"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-foreground truncate">{selectedFile?.name}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {(selectedFile?.size / 1024).toFixed(1)} KB • {t("imageReady")}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={removeSelectedFile}
                    className="text-destructive hover:bg-destructive/10 rounded-xl"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <Alert variant="destructive" className="rounded-2xl">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex-1 space-y-2">
                  <AlertTitle className="font-bold">{isQuotaError ? t("quotaExceededTitle") : "Notice"}</AlertTitle>
                  <AlertDescription className="text-xs leading-relaxed">{error}</AlertDescription>
                  {isQuotaError && (
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => setShowUpgradeModal(true)}
                      className="mt-1 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl text-xs gap-1.5 shadow-md"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{t("upgradeToPro")} (Unlimited)</span>
                    </Button>
                  )}
                </div>
              </Alert>
            )}

            {/* Submit Button */}
            <div className="pt-2">
              <Button
                type="submit"
                disabled={loading || !question.trim()}
                className="w-full sm:w-auto px-8 py-5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold shadow-lg shadow-emerald-600/20 text-sm gap-2"
              >
                {loading ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    <span>{t("orchestratingBtn")}</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>{t("runAnalysisBtn")}</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results View */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Agent Workflow Execution Status Strip */}
          <Card className="border-border bg-muted/20">
            <CardContent className="p-4">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-500" />
                {t("workflowChainTitle")}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {result.agent_activity?.map((act, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-background border border-border flex flex-col justify-between gap-1 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground capitalize">
                        {act.agent.replace("-", " ")}
                      </span>
                      <Badge
                        variant="secondary"
                        className={`text-[10px] ${
                          act.status === "success"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : act.status === "skipped"
                            ? "bg-slate-500/10 text-slate-500"
                            : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                        }`}
                      >
                        {act.status}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-muted-foreground line-clamp-2">{act.details}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Primary Grounded Advisory Card */}
          <Card className="border-emerald-500/40 bg-card shadow-xl overflow-hidden">
            <CardHeader className="border-b border-border bg-emerald-500/5 pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-emerald-600 text-white text-xs">
                      {result.crop ? `Crop: ${result.crop.toUpperCase()}` : "Crop: General"}
                    </Badge>
                    {result.detected_language && (
                      <Badge variant="outline" className="text-xs">
                        Lang: {result.detected_language}
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-xl font-extrabold text-foreground">
                    {t("advisoryHeading")}
                  </CardTitle>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleTextToSpeech(result.advisory)}
                    className="rounded-xl text-xs gap-1.5"
                  >
                    {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                    <span>{isSpeaking ? t("stopAudio") : t("listenAudio")}</span>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyAdvisory}
                    className="rounded-xl text-xs gap-1.5"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? t("copiedText") : t("copyText")}</span>
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-6 space-y-6">
              {/* Formatted Markdown Advisory Content */}
              <div className="prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed whitespace-pre-wrap">
                {result.advisory}
              </div>

              {/* Safety Note Alert */}
              {result.safety_note && (
                <div className="flex items-start gap-3 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-200 text-xs leading-relaxed">
                  <ShieldAlert className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
                  <div>
                    <span className="font-bold">{t("responsibleNotice")}: </span>
                    {result.safety_note}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Vision Diagnosis Breakdown (if Vision Agent returned output) */}
          {result.vision_result && result.vision_result.status === "success" && (
            <Card className="border-teal-500/30 bg-card shadow-lg">
              <CardHeader className="pb-3 border-b border-border">
                <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                  <Leaf className="w-4 h-4 text-teal-600" />
                  Agent 1: Leaf Pathology & Grad-CAM Visual Explainability
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Diagnostic Summary */}
                  <div className="space-y-4">
                    <div className="p-4 rounded-2xl bg-teal-500/10 border border-teal-500/20 space-y-2">
                      <p className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                        {t("primaryDiagnosis")}
                      </p>
                      <h4 className="text-lg font-black text-foreground">{result.vision_result.prediction}</h4>
                      <div className="flex items-center gap-3 pt-1">
                        <Badge className="bg-teal-600 text-white text-xs">
                          {t("confidenceScore")}: {(result.vision_result.confidence * 100).toFixed(1)}%
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {t("severityLevel")}: {result.vision_result.severity_level || "Moderate"}
                        </Badge>
                      </div>
                    </div>

                    {/* Alternative Predictions */}
                    {result.vision_result.alternatives?.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-muted-foreground">{t("alternativeDiagnoses")}:</p>
                        <div className="space-y-1.5">
                          {result.vision_result.alternatives.map((alt, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between text-xs p-2 rounded-xl bg-muted/30"
                            >
                              <span className="font-medium text-foreground">{alt.disease}</span>
                              <span className="text-muted-foreground">{(alt.confidence * 100).toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Grad-CAM Heatmap Image */}
                  <div className="flex flex-col items-center justify-center p-4 rounded-2xl bg-muted/20 border border-border text-center space-y-3">
                    {result.vision_result.gradcam_base64 ? (
                      <div>
                        <img
                          src={`data:image/png;base64,${result.vision_result.gradcam_base64}`}
                          alt="Grad-CAM Heatmap"
                          className="max-h-48 rounded-xl border border-border shadow-md object-contain mx-auto"
                        />
                        <p className="text-[11px] text-muted-foreground mt-2">
                          {t("heatmapExplain")}
                        </p>
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">No heatmap generated for this sample.</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Research Evidence & Citations */}
          {result.sources?.length > 0 && (
            <Card className="border-border bg-card shadow-lg">
              <CardHeader className="pb-3 border-b border-border">
                <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-emerald-600" />
                  {t("citationsHeading")}
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  {t("citationsSub")}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {result.sources.map((src, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-2xl bg-muted/30 border border-border space-y-1 hover:border-emerald-500/40 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span className="text-xs font-bold text-foreground truncate">{src.source}</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                        <span>{t("pageLabel")}: {src.page ?? 1}</span>
                        {src.similarity_score && (
                          <Badge variant="secondary" className="text-[10px]">
                            {t("matchScore")}: {(src.similarity_score * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};
