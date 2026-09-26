import React, { useState, useEffect, useRef } from "react";
import { 
  Bot, 
  Mic, 
  MicOff, 
  Send, 
  Sparkles, 
  Volume2, 
  VolumeX, 
  Clock, 
  RotateCcw, 
  CheckCircle2, 
  AlertCircle, 
  Leaf, 
  HelpCircle, 
  ArrowRight,
  Zap,
  Activity,
  ChevronRight,
  Copy,
  Check,
  X,
  Radio,
  ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { agentService } from "@/services/api";
import { useQuota } from "@/context/QuotaContext";
import { QuotaWidget } from "@/components/QuotaWidget";

const QUICK_SUGGESTIONS = [
  {
    crop: "Tomato (තක්කාලි)",
    icon: "🍅",
    text: "මගේ තක්කාලි වල කළුපාට ලප තියෙනවා (My tomato leaves have black spots)",
    category: "Disease Diagnosis"
  },
  {
    crop: "Paddy (වී / ගොයම්)",
    icon: "🌾",
    text: "ගොයම් පැළ කහ වෙලා මැලවෙනවා, යෙදිය යුතු පොහොර මොනවාද?",
    category: "Fertilizer & Health"
  },
  {
    crop: "Chili (මිරිස්)",
    icon: "🌶️",
    text: "මිරිස් කොළ හැකිලිලා සුදු මැස්සන් ඉන්නවා (Chili leaf curl & whiteflies)",
    category: "Pest & Disease"
  },
  {
    crop: "Brinjal (වම්බටු)",
    icon: "🍆",
    text: "වම්බටු ගෙඩි කුණුවීම සහ කරටි පණුවා මර්දනය කරන්නේ කොහොමද?",
    category: "Organic Remedy"
  },
  {
    crop: "Tomato (English)",
    icon: "🍅",
    text: "My tomato leaves are turning yellow with dark brown spots.",
    category: "Disease Diagnosis"
  },
  {
    crop: "Cabbage / Market",
    icon: "🥬",
    text: "දඹුල්ල ආර්ථික මධ්‍යස්ථානයේ ගෝවා තොග මිල කීයද?",
    category: "Market Rates"
  }
];


export const AgentQueryAssistant = ({ onCropDetected }) => {
  const { updateQuotaFromResponse, openUpgradeModal, t } = useQuota();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  
  // Voice recognition states
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [autoTriggerOnVoice, setAutoTriggerOnVoice] = useState(true);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const [language, setLanguage] = useState("si-LK");
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [voiceNetworkBlocked, setVoiceNetworkBlocked] = useState(false);
  
  // Text to Speech states
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);

  // Microservice status
  const [agentStatus, setAgentStatus] = useState({ status: "checking", mode: "integrated" });

  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const [micStream, setMicStream] = useState(null);

  // Initialize Speech Recognition & Load History
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceSupported(false);
    } else {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = language || "si-LK";

        recognition.onstart = () => {
          setIsListening(true);
          setError(null);
          setVoiceNetworkBlocked(false);
        };

        recognition.onresult = (event) => {
          let currentTranscript = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              currentTranscript = transcript;
              setQuestion(transcript);
              setInterimTranscript("");
              setShowVoiceModal(false);
              
              // Auto submit if option is enabled
              if (autoTriggerOnVoice && transcript.trim().length > 0) {
                handleAutoSubmit(transcript.trim());
              }
            } else {
              currentTranscript += transcript;
              setInterimTranscript(currentTranscript);
            }
          }
        };

        recognition.onerror = (event) => {
          console.warn("Speech recognition event notice:", event.error);
          setIsListening(false);
          setInterimTranscript("");

          if (event.error === "network") {
            setVoiceNetworkBlocked(true);
          } else if (event.error === "not-allowed" || event.error === "permission-denied") {
            setError("Microphone access was denied. Please allow microphone permissions in your browser.");
          }
        };

        recognition.onend = () => {
          setIsListening(false);
          setInterimTranscript("");
        };

        recognitionRef.current = recognition;
      } catch (e) {
        console.error("SpeechRecognition initialization error:", e);
      }
    }

    loadHistory();
    checkAgentHealth();

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // ignore
        }
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
      if (micStream) {
        micStream.getTracks().forEach(t => t.stop());
      }
    };
  }, [language, autoTriggerOnVoice]);

  const changeVoiceLanguage = (newLang) => {
    setLanguage(newLang);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {}
      setTimeout(() => {
        try {
          if (recognitionRef.current) {
            recognitionRef.current.lang = newLang;
            recognitionRef.current.start();
            setIsListening(true);
          }
        } catch (err) {
          console.warn("Restart recognition notice:", err);
        }
      }, 100);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await agentService.getQueryHistory(10);
      setHistory(data || []);
    } catch (err) {
      console.warn("Could not load query history:", err);
    }
  };

  const checkAgentHealth = async () => {
    try {
      const res = await agentService.checkAgent1Status();
      setAgentStatus(res);
    } catch {
      setAgentStatus({ status: "online", mode: "integrated-nlp" });
    }
  };

  const openVoiceAssistant = async () => {
    setShowVoiceModal(true);
    setError(null);
    setInterimTranscript("");

    // Attempt to prompt/verify microphone permissions
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setMicStream(stream);
      } catch (err) {
        console.warn("getUserMedia error:", err);
      }
    }

    if (voiceSupported && recognitionRef.current) {
      try {
        recognitionRef.current.lang = language || "si-LK";
        recognitionRef.current.start();
      } catch (err) {
        console.warn("Recognition start notice:", err);
      }
    }
  };

  const stopVoiceListening = () => {
    try {
      recognitionRef.current?.stop();
    } catch (e) {
      // ignore
    }
    setIsListening(false);
    setShowVoiceModal(false);
  };

  const triggerVoicePreset = (voiceText) => {
    setShowVoiceModal(false);
    setError(null);
    setQuestion(voiceText);
    executeQuery(voiceText, "voice", true);
  };

  const handleAutoSubmit = async (textToSubmit) => {
    await executeQuery(textToSubmit, "voice", true);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!question.trim()) return;
    await executeQuery(question.trim(), "text", false);
  };

  const executeQuery = async (queryText, inputMode = "text", autoTriggered = false) => {
    setLoading(true);
    setError(null);
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }

    try {
      const response = await agentService.queryAgent1({
        question: queryText,
        input_mode: inputMode,
        auto_triggered: autoTriggered,
        language: language.split("-")[0]
      });

      if (response?.quota_status) {
        updateQuotaFromResponse(response.quota_status);
      }

      setResult(response);
      loadHistory();

      // Trigger callback if parent wants to know about detected crop
      const detectedCrop = response?.agent_response?.agent_1_result?.crop;
      if (detectedCrop && onCropDetected) {
        onCropDetected(detectedCrop);
      }

      // Auto speak response summary if voice was used
      if (inputMode === "voice" && response?.agent_response?.advisory_summary) {
        speakText(response.agent_response.advisory_summary);
      }
    } catch (err) {
      console.error("Agent 1 Query Error:", err);
      const isQuota429 = err.response?.status === 429;
      const detailMsg = err.response?.data?.detail?.message || err.response?.data?.detail || "Failed to process query through Agent 1. Please try again.";
      setError({
        message: typeof detailMsg === "object" ? JSON.stringify(detailMsg) : detailMsg,
        isQuotaExceeded: isQuota429
      });
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text) => {
    if (!synthRef.current) return;

    if (isSpeaking) {
      synthRef.current.cancel();
      setIsSpeaking(false);
      return;
    }

    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    synthRef.current.speak(utterance);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const selectSuggestion = (text) => {
    setError(null);
    setQuestion(text);
    executeQuery(text, "text", false);
  };

  const agent1Data = result?.agent_response?.agent_1_result;
  const advisory = result?.agent_response?.advisory_summary || result?.agent_response?.agent_2_result?.message;

  return (
    <div className="space-y-6">
      {/* Agent 1 Header Banner */}
      <div className="agentic-hero rounded-3xl text-white p-6 shadow-xl shadow-emerald-900/20 ring-1 ring-white/10 relative overflow-hidden">
        <div className="absolute -right-8 -bottom-8 w-48 h-48 bg-emerald-400/20 rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center text-emerald-200 shadow-inner">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight">Agent 1: Smart NLP & Advisory Agent</h2>
                <Badge variant="secondary" className="bg-white/10 backdrop-blur text-emerald-100 border-white/20 text-[11px] gap-1.5">
                  <span className="agent-dot" />
                  {agentStatus.status === "online" ? "Active" : "Ready"}
                </Badge>
              </div>
              <p className="text-xs text-emerald-100/70 mt-0.5">
                Intelligent Natural Language Processing, Symptom Detection & Multi-Agent Dispatcher
              </p>
            </div>
          </div>

          {/* Controls: Language & Auto-Trigger */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-xs rounded-full bg-white/10 backdrop-blur border border-white/20 text-emerald-50 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-300 [&>option]:text-slate-900"
            >
              <option value="en-US">English (US/UK)</option>
              <option value="si-LK">Sinhala (Sri Lanka)</option>
              <option value="ta-LK">Tamil (Sri Lanka)</option>
            </select>

            <button
              type="button"
              onClick={() => setAutoTriggerOnVoice(!autoTriggerOnVoice)}
              className={`text-xs px-3 py-1.5 rounded-full border backdrop-blur transition-all flex items-center gap-1.5 ${
                autoTriggerOnVoice
                  ? "bg-emerald-400/20 border-emerald-300/40 text-emerald-100"
                  : "bg-white/5 border-white/15 text-slate-300"
              }`}
              title="Automatically sends query to Agent 1 when you finish speaking"
            >
              <Zap className={`w-3 h-3 ${autoTriggerOnVoice ? "text-amber-300" : "text-slate-500"}`} />
              Auto-Call on Voice: {autoTriggerOnVoice ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </div>

      {/* Main Interactive Query Box */}
      <Card className="glass-card shadow-xl shadow-emerald-900/5 border-emerald-500/20 rounded-3xl overflow-hidden">
        <div className="h-1 w-full bg-gradient-to-r from-emerald-500 via-teal-400 to-amber-400" />
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/30">
                <Sparkles className="w-4 h-4" />
              </span>
              Ask Farming Question (Text or Voice)
            </span>
            <span className="text-xs text-muted-foreground font-normal">
              Press Enter to submit
            </span>
          </CardTitle>
          <CardDescription>
            Speak or type crop symptoms, fertilizer questions, or market rate inquiries in natural language.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive" className="py-3 relative border-rose-500/30 bg-rose-500/10">
              <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5" />
              <div className="flex-1">
                <AlertTitle className="text-xs font-semibold text-rose-600 dark:text-rose-400">
                  {error.isQuotaExceeded ? (t?.quota_exceeded || "Daily Limit Exceeded") : "Query Notice"}
                </AlertTitle>
                <AlertDescription className="text-xs text-rose-700 dark:text-rose-300 mt-0.5">
                  {typeof error === "string" ? error : error.message}
                </AlertDescription>
                {error.isQuotaExceeded && (
                  <div className="mt-2.5 flex items-center gap-2">
                    <Button
                      size="sm"
                      onClick={openUpgradeModal}
                      className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold h-7 px-3 text-xs rounded-lg shadow-sm"
                    >
                      <Sparkles className="w-3 h-3 mr-1 text-slate-950" />
                      {t?.upgrade_pro || "Upgrade to Unlimited Pro"}
                    </Button>
                  </div>
                )}
              </div>
              <button 
                type="button" 
                onClick={() => setError(null)}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </Alert>
          )}

          {/* Text & Voice Input Area */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => {
                  setQuestion(e.target.value);
                  if (error) setError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                placeholder="e.g. My tomato leaves are turning yellow with brown spots, what should I do?"
                rows={3}
                className="w-full rounded-2xl border border-input bg-background/80 backdrop-blur p-4 pr-28 pb-14 text-sm focus:outline-none focus:border-emerald-500/60 focus:ring-4 focus:ring-emerald-500/15 focus:shadow-lg focus:shadow-emerald-500/10 transition-all resize-none"
              />

              {/* Action Buttons inside Textarea */}
              <div className="absolute right-2.5 bottom-3 flex items-center gap-1.5">
                {/* Voice Input Button */}
                <Button
                  type="button"
                  size="sm"
                  onClick={openVoiceAssistant}
                  variant="secondary"
                  className="h-9 px-3 rounded-xl hover:bg-emerald-100 hover:text-emerald-700 dark:hover:bg-emerald-950 transition-all gap-1.5 border border-emerald-500/30"
                  title="Click to speak or use voice assistant"
                >
                  <Mic className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-xs font-medium hidden sm:inline">Voice</span>
                </Button>

                {/* Send Button */}
                <Button
                  type="submit"
                  size="sm"
                  disabled={loading || !question.trim()}
                  className="h-9 px-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-md shadow-emerald-600/30 gap-1.5"
                >
                  {loading ? (
                    <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  <span className="hidden sm:inline text-xs font-medium">
                    {loading ? "Analyzing..." : "Ask Agent"}
                  </span>
                </Button>
              </div>
            </div>
          </form>

          {/* Quick Suggestions Chips */}
          <div className="space-y-1.5 pt-1">
            <p className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <HelpCircle className="w-3 h-3 text-emerald-600" />
              Quick Sri Lankan Farming Presets:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_SUGGESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => selectSuggestion(item.text)}
                  className="text-xs px-3 py-1.5 rounded-full bg-background/70 backdrop-blur hover:bg-emerald-500/10 hover:text-emerald-700 dark:hover:text-emerald-300 border border-border/70 hover:border-emerald-500/40 hover:-translate-y-0.5 hover:shadow-md hover:shadow-emerald-500/10 transition-all text-left flex items-center gap-1.5"
                >
                  <span>{item.icon}</span>
                  <span className="font-medium text-[11px] truncate max-w-[220px] sm:max-w-none">{item.text}</span>
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Voice Assistant Modal / Overlay */}
      {showVoiceModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <Card className="max-w-lg w-full glass-card border-emerald-500/40 shadow-2xl relative overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between bg-gradient-to-r from-emerald-950/60 to-slate-900">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white">
                  <Mic className="w-4 h-4 animate-pulse" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Agent 1 Voice Assistant</h3>
                  <p className="text-[11px] text-emerald-200/70">Speak clearly into your microphone</p>
                </div>
              </div>
              <button 
                onClick={stopVoiceListening}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <CardContent className="p-6 space-y-5 text-center">
              {/* Language Selection Tabs */}
              <div className="flex items-center justify-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-emerald-500/30">
                <button
                  type="button"
                  onClick={() => changeVoiceLanguage("si-LK")}
                  className={`flex-1 text-xs py-1.5 px-2.5 rounded-lg font-bold transition-all flex items-center justify-center gap-1 ${
                    language === "si-LK"
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  🇱🇰 සිංහල (Sinhala)
                </button>
                <button
                  type="button"
                  onClick={() => changeVoiceLanguage("en-US")}
                  className={`flex-1 text-xs py-1.5 px-2.5 rounded-lg font-bold transition-all flex items-center justify-center gap-1 ${
                    language === "en-US"
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  🇬🇧 English
                </button>
                <button
                  type="button"
                  onClick={() => changeVoiceLanguage("ta-LK")}
                  className={`flex-1 text-xs py-1.5 px-2.5 rounded-lg font-bold transition-all flex items-center justify-center gap-1 ${
                    language === "ta-LK"
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  🇱🇰 தமிழ் (Tamil)
                </button>
              </div>

              {/* Sound Wave Animation */}
              <div className="flex items-center justify-center gap-1.5 py-3">
                <span className="w-1.5 h-6 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1.5 h-12 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-16 bg-emerald-300 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-10 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
              </div>

              {/* Interim Live Transcript or Listening Prompt */}
              <div className="p-4 rounded-xl bg-secondary/50 border border-border min-h-[60px] flex items-center justify-center">
                {interimTranscript ? (
                  <p className="text-sm font-medium text-foreground italic">
                    "{interimTranscript}"
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    {isListening
                      ? language === "si-LK"
                        ? "🎙️ සවන් දෙමින්... කරුණාකර ඔබගේ ගැටළුව සිංහලෙන් පවසන්න."
                        : language === "ta-LK"
                        ? "🎙️ கேட்கிறது... உங்கள் கேள்வியை தமிழில் பேசுங்கள்."
                        : "🎙️ Listening... Speak your crop symptoms or question now."
                      : "Microphone active. Ready for your voice."}
                  </p>
                )}
              </div>

              {/* Tip / Brave browser helper if network blocked */}
              {voiceNetworkBlocked && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-left text-xs text-amber-800 dark:text-amber-200 space-y-1">
                  <div className="font-semibold flex items-center gap-1.5">
                    <Radio className="w-3.5 h-3.5 text-amber-600" />
                    Browser Notice (Brave / Private Network):
                  </div>
                  <p className="text-[11px] leading-relaxed text-muted-foreground">
                    If using Brave, enable <em>"Google services for voice recognition"</em> in <code className="bg-amber-100 dark:bg-amber-950 px-1 py-0.5 rounded text-[10px]">brave://settings/system</code>, or tap any voice query below to auto-call Agent 1:
                  </p>
                </div>
              )}

              {/* 1-Click Voice Trigger Presets */}
              <div className="space-y-2 text-left">
                <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
                  Quick Voice Commands (Auto-Call Agent 1):
                </span>
                <div className="grid grid-cols-1 gap-2">
                  {QUICK_SUGGESTIONS.slice(0, 4).map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => triggerVoicePreset(item.text)}
                      className="p-2.5 rounded-xl bg-background/80 hover:bg-emerald-500/10 hover:border-emerald-500/40 border border-border text-left transition-all flex items-center justify-between group"
                    >
                      <div className="flex items-center gap-2 truncate pr-2">
                        <span className="text-base">{item.icon}</span>
                        <div className="truncate">
                          <p className="text-xs font-medium text-foreground group-hover:text-emerald-600 transition-colors truncate">
                            {item.text}
                          </p>
                          <span className="text-[10px] text-muted-foreground">{item.category}</span>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-[10px] font-normal group-hover:bg-emerald-600 group-hover:text-white transition-colors flex-shrink-0">
                        Auto-Call
                      </Badge>
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={stopVoiceListening}
                  className="w-full text-xs"
                >
                  Cancel Voice Input
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Agent 1 Analysis & Advisory Results */}
      {result && (
        <Card className="glass-card border-emerald-500/30 shadow-xl shadow-emerald-900/10 rounded-3xl overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="h-1 w-full bg-gradient-to-r from-emerald-500 via-teal-400 to-amber-400" />
          <div className="bg-[radial-gradient(40rem_10rem_at_0%_0%,rgba(16,185,129,0.16),transparent_70%)] p-4 border-b border-border/60 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/30">
                <CheckCircle2 className="w-4 h-4" />
              </span>
              <h3 className="font-bold text-foreground text-base">Agent 1 NLP Analysis & Diagnostic Result</h3>
            </div>
            
            <div className="flex items-center gap-2">
              {advisory && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => speakText(advisory)}
                  className="h-8 text-xs gap-1.5"
                  title="Listen to advisory audio readout"
                >
                  {isSpeaking ? (
                    <>
                      <VolumeX className="w-3.5 h-3.5 text-red-500 animate-pulse" />
                      <span>Stop Voice</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Listen Aloud</span>
                    </>
                  )}
                </Button>
              )}

              <Button
                size="sm"
                variant="ghost"
                onClick={() => copyToClipboard(advisory || JSON.stringify(agent1Data))}
                className="h-8 w-8 p-0 text-muted-foreground"
                title="Copy result"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              </Button>
            </div>
          </div>

          <CardContent className="p-6 space-y-6">
            {/* Entity Extraction Breakdown Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Identified Crop */}
              <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-500/20">
                <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 uppercase tracking-wider block mb-1">
                  Identified Crop
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <Leaf className="w-5 h-5 text-emerald-600" />
                  <span className="font-extrabold text-lg capitalize text-foreground">
                    {agent1Data?.crop || "General / Not Specified"}
                  </span>
                </div>
              </div>

              {/* Detected Symptoms */}
              <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-500/20">
                <span className="text-[11px] font-semibold text-amber-700 dark:text-amber-300 uppercase tracking-wider block mb-1">
                  Extracted Symptoms
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {agent1Data?.symptoms && agent1Data.symptoms.length > 0 ? (
                    agent1Data.symptoms.map((sym, i) => (
                      <Badge key={i} variant="secondary" className="bg-amber-500/20 text-amber-800 dark:text-amber-200 border-amber-400/30 text-xs">
                        {sym}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground italic">No pathological symptoms detected</span>
                  )}
                </div>
              </div>

              {/* Classified Intent */}
              <div className="p-4 rounded-xl bg-teal-50/60 dark:bg-teal-950/30 border border-teal-500/20">
                <span className="text-[11px] font-semibold text-teal-700 dark:text-teal-300 uppercase tracking-wider block mb-1">
                  Classified Intent
                </span>
                <div className="mt-1">
                  <Badge variant="outline" className="border-teal-500/40 text-teal-700 dark:text-teal-300 text-xs font-semibold capitalize">
                    {agent1Data?.intent || "General Agriculture"}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Advisory Actionable Advice */}
            {advisory && (
              <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50/80 to-teal-50/50 dark:from-slate-900 dark:to-emerald-950/30 border border-emerald-500/20 space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                    Agent 1 Advisory Guidance
                  </h4>
                </div>
                <p className="text-sm text-foreground/90 leading-relaxed font-normal">
                  {advisory}
                </p>
              </div>
            )}

            {/* Multi-Agent Orchestration Bridge Status */}
            <div className="pt-2 border-t border-border flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs text-muted-foreground gap-2">
              <div className="flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Agent Pipeline: <strong>Query NLP (Agent 1)</strong></span>
                <ArrowRight className="w-3 h-3 text-muted-foreground" />
                <span className="text-foreground font-medium">Diagnostic Knowledge Base (Agent 2)</span>
              </div>
              <span className="text-[11px] text-muted-foreground">
                Triggered via: <strong className="capitalize">{result?.input_mode || "Text"} Input</strong>
                {result?.auto_triggered && " (Voice Auto-Fired)"}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Consultation History */}
      {history && history.length > 0 && (
        <Card className="glass-card">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-600" />
                Recent Agricultural Inquiries
              </span>
              <Badge variant="secondary" className="text-[10px]">
                {history.length} Sessions Logged
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="divide-y divide-border/60 max-h-60 overflow-y-auto pr-1">
              {history.map((item, idx) => {
                const crop = item?.agent_response?.agent_1_result?.crop;
                const intent = item?.agent_response?.agent_1_result?.intent;
                const dateStr = item?.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "";

                return (
                  <div
                    key={item.id || idx}
                    onClick={() => {
                      setQuestion(item.question);
                      setResult(item);
                    }}
                    className="py-2.5 px-3 flex items-center justify-between hover:bg-secondary/60 rounded-xl cursor-pointer transition-all group"
                  >
                    <div className="space-y-0.5 truncate pr-3">
                      <p className="text-xs font-medium text-foreground group-hover:text-emerald-600 transition-colors truncate">
                        "{item.question}"
                      </p>
                      <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                        {crop && (
                          <span className="capitalize font-semibold text-emerald-600">
                            🌿 {crop}
                          </span>
                        )}
                        {intent && <span>• {intent}</span>}
                        {item.input_mode === "voice" && <span>• 🎙️ Voice</span>}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[10px] text-muted-foreground">{dateStr}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
