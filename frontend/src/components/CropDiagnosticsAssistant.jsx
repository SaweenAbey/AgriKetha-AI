import React, { useState, useEffect, useRef } from "react";
import {
  Leaf,
  UploadCloud,
  Camera,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Activity,
  Layers,
  Volume2,
  VolumeX,
  Copy,
  Check,
  RotateCcw,
  Eye,
  ShieldCheck,
  ChevronRight,
  Info,
  Clock,
  Flame,
  Bug,
  HelpCircle,
  FileImage,
  Crosshair,
  Radio,
  Sliders,
  X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { visionService } from "@/services/api";
import { useQuota } from "@/context/QuotaContext";
import { QuotaWidget } from "@/components/QuotaWidget";

const PRESET_LEAF_SAMPLES = [
  {
    name: "Tomato Early Blight",
    crop: "Tomato",
    icon: "🍅",
    description: "Alternaria solani concentric leaf spots",
    svgColor: "#ef4444",
    sampleType: "tomato_blight",
    // Synthetic SVG canvas generator data
    seedText: "Tomato leaf with dark concentric circular target spots and yellow chlorotic halos"
  },
  {
    name: "Rice Brown Spot",
    crop: "Rice",
    icon: "🌾",
    description: "Bipolaris oryzae fungal lesions",
    svgColor: "#d97706",
    sampleType: "rice_spot",
    seedText: "Rice leaf with oval reddish brown spots with gray central necrosis"
  },
  {
    name: "Chili Leaf Curl",
    crop: "Chili",
    icon: "🌶️",
    description: "Begomovirus vector stunting & curling",
    svgColor: "#f59e0b",
    sampleType: "chili_curl",
    seedText: "Chili pepper leaf with upward cup curling, puckering, and thickened veins"
  },
  {
    name: "Brinjal Fruit Borer & Rot",
    crop: "Brinjal",
    icon: "🍆",
    description: "Phomopsis fruit rot and wilt",
    svgColor: "#8b5cf6",
    sampleType: "brinjal_rot",
    seedText: "Brinjal leaf with withered tip necrosis and sunken brown circular spots"
  },
  {
    name: "Healthy Tomato Leaf",
    crop: "Tomato",
    icon: "🍃",
    description: "No fungal or viral lesions",
    svgColor: "#10b981",
    sampleType: "healthy_leaf",
    seedText: "Vibrant healthy green foliage with clear vascular veins and zero lesions"
  }
];

// Helper to generate a realistic SVG canvas blob for presets if user clicks presets
function generatePresetBlob(sampleType, name) {
  const canvas = document.createElement("canvas");
  canvas.width = 400;
  canvas.height = 400;
  const ctx = canvas.getContext("2d");

  // Background leaf base gradient
  const bgGrad = ctx.createLinearGradient(0, 0, 400, 400);
  if (sampleType === "healthy_leaf") {
    bgGrad.addColorStop(0, "#2d6a4f");
    bgGrad.addColorStop(0.5, "#40916c");
    bgGrad.addColorStop(1, "#52b788");
  } else if (sampleType === "tomato_blight") {
    bgGrad.addColorStop(0, "#3d5a40");
    bgGrad.addColorStop(0.6, "#5c6b3c");
    bgGrad.addColorStop(1, "#445028");
  } else if (sampleType === "rice_spot") {
    bgGrad.addColorStop(0, "#4f772d");
    bgGrad.addColorStop(0.5, "#90a955");
    bgGrad.addColorStop(1, "#a3b18a");
  } else {
    bgGrad.addColorStop(0, "#386641");
    bgGrad.addColorStop(0.7, "#6a994e");
    bgGrad.addColorStop(1, "#bc4749");
  }
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, 400, 400);

  // Draw Leaf Shape
  ctx.beginPath();
  ctx.moveTo(200, 30);
  ctx.bezierCurveTo(340, 90, 370, 280, 200, 370);
  ctx.bezierCurveTo(30, 280, 60, 90, 200, 30);
  ctx.fillStyle = sampleType === "healthy_leaf" ? "#38b000" : "#4f772d";
  ctx.fill();
  ctx.lineWidth = 4;
  ctx.strokeStyle = "#1b4332";
  ctx.stroke();

  // Draw Central Vein
  ctx.beginPath();
  ctx.moveTo(200, 35);
  ctx.quadraticCurveTo(195, 200, 200, 370);
  ctx.strokeStyle = sampleType === "healthy_leaf" ? "#70e000" : "#aacc00";
  ctx.lineWidth = 4;
  ctx.stroke();

  // Draw Secondary Veins
  for (let y = 80; y <= 320; y += 40) {
    ctx.beginPath();
    ctx.moveTo(200, y);
    ctx.quadraticCurveTo(260, y - 10, 300, y - 25);
    ctx.moveTo(200, y);
    ctx.quadraticCurveTo(140, y - 10, 100, y - 25);
    ctx.strokeStyle = "rgba(255,255,255,0.3)";
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // Draw Pathology lesions if not healthy
  if (sampleType === "tomato_blight") {
    // Concentric dark rings
    [[160, 150, 35], [260, 220, 45], [180, 270, 30]].forEach(([x, y, r]) => {
      ctx.beginPath();
      ctx.arc(x, y, r + 10, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(234, 179, 8, 0.4)"; // yellow halo
      ctx.fill();

      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = "#451a03";
      ctx.fill();

      ctx.beginPath();
      ctx.arc(x, y, r * 0.6, 0, Math.PI * 2);
      ctx.strokeStyle = "#78350f";
      ctx.lineWidth = 3;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(x, y, r * 0.25, 0, Math.PI * 2);
      ctx.fillStyle = "#1c1917";
      ctx.fill();
    });
  } else if (sampleType === "rice_spot") {
    // Reddish-brown oval spots
    [[190, 120, 25, 10], [220, 190, 35, 15], [170, 260, 30, 12], [230, 310, 20, 8]].forEach(([x, y, rx, ry]) => {
      ctx.beginPath();
      ctx.ellipse(x, y, rx, ry, Math.PI / 4, 0, Math.PI * 2);
      ctx.fillStyle = "#7f1d1d";
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(x, y, rx * 0.5, ry * 0.5, Math.PI / 4, 0, Math.PI * 2);
      ctx.fillStyle = "#e2e8f0";
      ctx.fill();
    });
  } else if (sampleType === "chili_curl") {
    // Curling wrinkly texture
    ctx.strokeStyle = "rgba(254, 240, 138, 0.6)";
    ctx.lineWidth = 5;
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.arc(150 + i * 20, 120 + i * 35, 25, 0, Math.PI);
      ctx.stroke();
    }
  } else if (sampleType === "brinjal_rot") {
    ctx.beginPath();
    ctx.arc(200, 330, 50, 0, Math.PI * 2);
    ctx.fillStyle = "#3f1d38";
    ctx.fill();
    ctx.strokeStyle = "#831843";
    ctx.lineWidth = 6;
    ctx.stroke();
  }

  // Label banner
  ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
  ctx.fillRect(0, 360, 400, 40);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 14px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(`AgriKetha Sample: ${name}`, 200, 385);

  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      resolve(blob);
    }, "image/jpeg", 0.95);
  });
}

export const CropDiagnosticsAssistant = () => {
  const { updateQuotaFromResponse, openUpgradeModal, t } = useQuota();
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [cropHint, setCropHint] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("sideBySide"); // 'sideBySide', 'gradcam', 'original'
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [visionStatus, setVisionStatus] = useState({ status: "checking", mode: "integrated" });
  const [activeTab, setActiveTab] = useState("bio"); // 'bio', 'chem', 'cultural'

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Load Vision Agent Status & Diagnostic History
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await visionService.checkVisionStatus();
        setVisionStatus(status);
      } catch (err) {
        setVisionStatus({ status: "online", mode: "integrated-vision-engine" });
      }
    };

    const loadHistory = async () => {
      try {
        const hist = await visionService.getDiagnosticHistory(10);
        setHistory(hist || []);
      } catch (err) {
        console.error("Failed to load vision history:", err);
      }
    };

    checkStatus();
    loadHistory();
  }, []);

  // Handle local image selection
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setSelectedImage(file.name);
      setResult(null);
      setError(null);
    }
  };

  // Handle Preset Leaf Selection
  const handlePresetSelect = async (preset) => {
    setLoading(true);
    setError(null);
    try {
      const blob = await generatePresetBlob(preset.sampleType, preset.name);
      const file = new File([blob], `${preset.sampleType}.jpg`, { type: "image/jpeg" });
      setImageFile(file);
      setCropHint(preset.crop);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setSelectedImage(preset.name);
      setResult(null);

      // Auto analyze preset immediately for instant farmer delight
      await performAnalysis(file, preset.crop);
    } catch (err) {
      console.error("Preset load error:", err);
      setError("Failed to load sample leaf template.");
    } finally {
      setLoading(false);
    }
  };

  // Perform Vision Diagnostic Analysis
  const performAnalysis = async (fileToUse = null, cropToUse = null) => {
    const file = fileToUse || imageFile;
    if (!file) {
      setError("Please select or capture a crop leaf image first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("image", file);
      if (cropToUse || cropHint) {
        formData.append("crop", cropToUse || cropHint);
      }
      if (notes) {
        formData.append("notes", notes);
      }

      const res = await visionService.analyzeImage(formData);

    if (res?.quota_status) {
      updateQuotaFromResponse(res.quota_status);
    }

    // Handle backend validation errors such as:
    // - Blurry image
    // - Dark image
    // - Bright image
    // - Unsupported / unrelated image
    if (res?.status === "error") {
      setResult(null);

      setError({
        message: res.message || "The image could not be analyzed.",
        isQuotaExceeded: false,
      });

      return;
    }

    setResult(res);

      // Refresh history
      try {
        const hist = await visionService.getDiagnosticHistory(10);
        setHistory(hist || []);
      } catch (hErr) {
        console.warn("Could not refresh history:", hErr);
      }
    } catch (err) {
      console.error("Vision Analysis Error:", err);
      const isQuota429 = err.response?.status === 429;
      const detailMsg = err.response?.data?.detail?.message || err.response?.data?.detail || "Vision analysis failed. Please try a clearer leaf photo.";
      setError({
        message: typeof detailMsg === "object" ? JSON.stringify(detailMsg) : detailMsg,
        isQuotaExceeded: isQuota429
      });
    } finally {
      setLoading(false);
    }
  };

  // Text-To-Speech for Treatment Advisory
  const handleToggleSpeak = () => {
    if (!synthRef.current || !result) return;

    if (isSpeaking) {
      synthRef.current.cancel();
      setIsSpeaking(false);
      return;
    }

    const advisory = result.treatment_advisory || {};
    const textToRead = `Crop Diagnosis: ${result.prediction} on ${result.crop || 'crop'}. Severity level is ${result.severity_level}. ` +
      `Biological recommendation: ${advisory.biological_control || ''}. ` +
      `Chemical treatment: ${advisory.chemical_control || ''}. ` +
      `Cultural practices: ${advisory.cultural_practices || ''}.`;

    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.cancel();
    synthRef.current.speak(utterance);
    setIsSpeaking(true);
  };

  // Copy Prescription to Clipboard
  const handleCopyPrescription = () => {
    if (!result) return;
    const advisory = result.treatment_advisory || {};
    const text = `🌿 AgriKetha-AI Crop Pathology Diagnostic Report\n` +
      `-----------------------------------------------\n` +
      `Crop: ${result.crop || 'Identified Crop'}\n` +
      `Diagnosis: ${result.prediction}\n` +
      `Confidence: ${(result.confidence * 100).toFixed(1)}%\n` +
      `Severity: ${result.severity_level} (${result.severity_percentage}%)\n\n` +
      `[1] Biological & Organic Control:\n${advisory.biological_control}\n\n` +
      `[2] Department of Agriculture Approved Chemical:\n${advisory.chemical_control}\n\n` +
      `[3] Cultural & Agronomic Management:\n${advisory.cultural_practices}\n\n` +
      `Generated by AgriKetha-AI Vision Agent`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const getSeverityBadgeColor = (level) => {
    const l = (level || "").toLowerCase();
    if (l.includes("low") || l.includes("healthy")) return "bg-emerald-500/10 text-emerald-600 border-emerald-500/30";
    if (l.includes("moderate")) return "bg-amber-500/10 text-amber-600 border-amber-500/30";
    return "bg-rose-500/10 text-rose-600 border-rose-500/30";
  };

  const getSeverityProgressColor = (level) => {
    const l = (level || "").toLowerCase();
    if (l.includes("low") || l.includes("healthy")) return "bg-emerald-500";
    if (l.includes("moderate")) return "bg-amber-500";
    return "bg-rose-500";
  };

  return (
    <div className="space-y-6">
      {/* Header with Engine Status Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-teal-900/90 via-emerald-950/80 to-slate-900 text-white p-6 rounded-3xl border border-teal-500/30 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-teal-500/20 border border-teal-400/30 flex items-center justify-center text-teal-300">
              <Leaf className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight">
                AI Vision Pathology & Leaf Diagnostics
              </h2>
              <p className="text-xs sm:text-sm text-teal-100/70">
                PyTorch Deep Learning with Grad-CAM Visual Explainability & DOA Treatment Prescriptions
              </p>
            </div>
          </div>
        </div>

        <div className="relative z-10 flex items-center gap-2.5">
          <Badge
            variant="outline"
            className="px-3 py-1.5 text-xs font-semibold rounded-full bg-teal-500/10 border-teal-400/40 text-teal-200 flex items-center gap-1.5 shadow-sm"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <Activity className="w-3.5 h-3.5" />
            {visionStatus.mode === "microservice" ? "PyTorch Model Active (:8002)" : "Integrated Vision Engine"}
          </Badge>
        </div>
      </div>

      {/* Preset Test Leaves Row */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            Quick Test Leaf Presets (Instant Demo)
          </span>
          <span className="text-[11px] text-muted-foreground hidden sm:inline">
            Click any leaf to run instant automated diagnosis
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {PRESET_LEAF_SAMPLES.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetSelect(preset)}
              disabled={loading}
              className="group flex flex-col items-start p-3 rounded-2xl border border-border/70 bg-card hover:bg-emerald-500/5 hover:border-emerald-500/50 hover:shadow-md transition-all text-left relative overflow-hidden"
            >
              <div className="flex items-center gap-1.5 w-full mb-1">
                <span className="text-base">{preset.icon}</span>
                <span className="text-xs font-bold text-foreground group-hover:text-emerald-600 transition-colors truncate">
                  {preset.crop}
                </span>
              </div>
              <span className="text-[11px] font-medium text-muted-foreground line-clamp-1">
                {preset.name}
              </span>
              <span className="text-[9px] text-muted-foreground/80 mt-1 line-clamp-1">
                {preset.description}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Upload & Preview on Left, Diagnostics on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Upload & Preview (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-border/80 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <FileImage className="w-4 h-4 text-teal-600" />
                Upload or Snap Leaf Photo
              </CardTitle>
              <CardDescription className="text-xs">
                Provide a clear close-up of the infected leaf area
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drop / Preview Zone */}
              <div
                onClick={() => !previewUrl && fileInputRef.current?.click()}
                className={`relative group rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center p-4 min-h-[260px] overflow-hidden ${previewUrl
                    ? "border-emerald-500/60 bg-emerald-950/5"
                    : "border-border hover:border-teal-500 hover:bg-teal-500/5 cursor-pointer"
                  }`}
              >
                {/* Laser Scanning Animation Overlay */}
                {loading && (
                  <div className="absolute inset-0 z-20 bg-slate-950/60 backdrop-blur-xs flex flex-col items-center justify-center p-4">
                    {/* Glowing Laser line */}
                    <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_15px_#10b981] animate-bounce top-1/3" />
                    <div className="w-12 h-12 rounded-full border-4 border-emerald-400 border-t-transparent animate-spin mb-3" />
                    <span className="text-xs font-bold text-white tracking-wide flex items-center gap-1.5">
                      <Crosshair className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                      PyTorch Neural Diagnostics & Grad-CAM...
                    </span>
                    <span className="text-[10px] text-emerald-200/80 mt-1">
                      Extracting lesion patches & calculating feature vectors
                    </span>
                  </div>
                )}

                {previewUrl ? (
                  <div className="relative w-full h-full flex flex-col items-center">
                    <img
                      src={previewUrl}
                      alt="Crop Leaf Preview"
                      className="max-h-64 w-full object-contain rounded-xl shadow-sm border border-border"
                    />
                    <div className="absolute top-2 right-2 flex gap-1.5">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 px-2 text-[11px] bg-background/80 backdrop-blur-md hover:bg-background shadow"
                        onClick={(e) => {
                          e.stopPropagation();
                          fileInputRef.current?.click();
                        }}
                      >
                        Change
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="h-7 px-2 text-[11px] shadow"
                        onClick={(e) => {
                          e.stopPropagation();
                          setPreviewUrl(null);
                          setImageFile(null);
                          setSelectedImage(null);
                          setResult(null);
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center space-y-2.5 p-4">
                    <div className="w-14 h-14 rounded-2xl bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                      <UploadCloud className="w-7 h-7" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        Click to upload or drag & drop
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Supports JPG, PNG, WEBP (High resolution leaf close-up)
                      </p>
                    </div>
                  </div>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <input
                  ref={cameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>

              {/* Action Buttons: Camera & Crop Selection */}
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => cameraInputRef.current?.click()}
                  className="text-xs gap-1.5 h-9"
                >
                  <Camera className="w-3.5 h-3.5 text-teal-600" />
                  Take Photo
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs gap-1.5 h-9"
                >
                  <FileImage className="w-3.5 h-3.5 text-emerald-600" />
                  Browse Files
                </Button>
              </div>

              {/* Optional Crop Category Hint */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                  <span>Crop Category</span>
                  <span className="text-[10px] text-muted-foreground">Assists model prior</span>
                </label>
                <div className="grid grid-cols-4 gap-1.5">
                  {["Tomato", "Rice", "Chili", "Brinjal"].map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setCropHint(cropHint === c ? "" : c)}
                      className={`text-xs py-1.5 px-2 rounded-xl border font-medium transition-all ${cropHint === c
                          ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                          : "bg-background border-border text-foreground hover:bg-muted"
                        }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Analyze Button */}
              <Button
                type="button"
                onClick={() => performAnalysis()}
                disabled={!imageFile || loading}
                className="w-full bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-bold h-11 text-sm rounded-xl shadow-lg shadow-emerald-600/20 gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Diagnosing Pathology...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Run AI Leaf Diagnostics
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Diagnostic Results & Explainability (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {error && (
            <Alert variant="destructive" className="py-3.5 rounded-2xl relative border-rose-500/30 bg-rose-500/10">
              <AlertCircle className="w-4 h-4 text-rose-500 mt-0.5" />
              <div className="flex-1">
                <AlertTitle className="text-xs font-semibold text-rose-600 dark:text-rose-400">
                  {error.isQuotaExceeded ? (t?.quota_exceeded || "Daily Limit Exceeded") : "Diagnostic Error"}
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
                className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </Alert>
          )}

          {result ? (
            <div className="space-y-4 animate-in fade-in-50 duration-300">
              {/* Top Result Banner */}
              <Card className="border-teal-500/40 shadow-xl bg-card overflow-hidden">
                <div className="bg-gradient-to-r from-teal-600 to-emerald-600 text-white p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className="bg-white/20 text-white border-none text-[10px] uppercase tracking-wider">
                        {result.crop || "Identified Crop"}
                      </Badge>
                      <span className="text-xs text-teal-100 font-medium">
                        {(result.confidence * 100).toFixed(1)}% Neural Confidence
                      </span>
                    </div>
                    <h3 className="text-lg sm:text-xl font-extrabold tracking-tight">
                      {result.prediction}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={handleToggleSpeak}
                      className="h-8 gap-1.5 text-xs bg-white text-teal-900 hover:bg-white/90 shadow font-semibold"
                    >
                      {isSpeaking ? <VolumeX className="w-3.5 h-3.5 text-rose-600" /> : <Volume2 className="w-3.5 h-3.5 text-teal-600" />}
                      {isSpeaking ? "Stop Voice" : "Listen Advisory"}
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={handleCopyPrescription}
                      className="h-8 gap-1.5 text-xs bg-teal-800/80 text-white hover:bg-teal-800 border border-teal-400/30"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? "Copied" : "Copy"}
                    </Button>
                  </div>
                </div>

                <CardContent className="p-5 space-y-5">
                  {/* Severity & Metrics Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/70 space-y-2">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-muted-foreground flex items-center gap-1.5">
                          <Flame className="w-3.5 h-3.5 text-rose-500" />
                          Pathological Severity Index
                        </span>
                        <Badge variant="outline" className={getSeverityBadgeColor(result.severity_level)}>
                          {result.severity_level} ({result.severity_percentage}%)
                        </Badge>
                      </div>
                      <div className="w-full bg-border rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full ${getSeverityProgressColor(result.severity_level)} transition-all duration-500`}
                          style={{ width: `${Math.min(100, Math.max(5, result.severity_percentage))}%` }}
                        />
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/70 space-y-1.5">
                      <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                        Urgency & Spread Risk
                      </span>
                      <p className="text-xs font-bold text-foreground">
                        {result.treatment_advisory?.urgency || "Moderate - Monitor closely over 48 hours"}
                      </p>
                    </div>
                  </div>

                  {/* Grad-CAM Explainability Section */}
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Eye className="w-3.5 h-3.5 text-teal-600" />
                        Grad-CAM Attention & Pathology Heatmap
                      </span>
                      {result.gradcam_base64 && (
                        <div className="flex gap-1">
                          <button
                            type="button"
                            onClick={() => setViewMode("sideBySide")}
                            className={`text-[10px] px-2 py-1 rounded-md font-semibold ${viewMode === "sideBySide" ? "bg-teal-600 text-white" : "bg-muted text-muted-foreground"}`}
                          >
                            Split View
                          </button>
                          <button
                            type="button"
                            onClick={() => setViewMode("gradcam")}
                            className={`text-[10px] px-2 py-1 rounded-md font-semibold ${viewMode === "gradcam" ? "bg-teal-600 text-white" : "bg-muted text-muted-foreground"}`}
                          >
                            Heatmap Only
                          </button>
                          <button
                            type="button"
                            onClick={() => setViewMode("original")}
                            className={`text-[10px] px-2 py-1 rounded-md font-semibold ${viewMode === "original" ? "bg-teal-600 text-white" : "bg-muted text-muted-foreground"}`}
                          >
                            Original
                          </button>
                        </div>
                      )}
                    </div>

                    {result.gradcam_base64 ? (
                      <div className="rounded-2xl border border-border/80 overflow-hidden bg-slate-950 p-2">
                        {viewMode === "sideBySide" && (
                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                              <span className="text-[10px] font-bold text-slate-300 block text-center">Original Crop Leaf</span>
                              <img
                                src={result.image_preview || previewUrl}
                                alt="Original Leaf"
                                className="w-full h-40 object-cover rounded-xl border border-slate-800"
                              />
                            </div>
                            <div className="space-y-1">
                              <span className="text-[10px] font-bold text-emerald-400 block text-center">Grad-CAM Lesion Heatmap</span>
                              <img
                                src={`data:image/png;base64,${result.gradcam_base64}`}
                                alt="Grad-CAM Attention Map"
                                className="w-full h-40 object-cover rounded-xl border border-emerald-500/40"
                              />
                            </div>
                          </div>
                        )}
                        {viewMode === "gradcam" && (
                          <img
                            src={`data:image/png;base64,${result.gradcam_base64}`}
                            alt="Grad-CAM Attention Map"
                            className="w-full h-56 object-contain rounded-xl"
                          />
                        )}
                        {viewMode === "original" && (
                          <img
                            src={result.image_preview || previewUrl}
                            alt="Original Leaf"
                            className="w-full h-56 object-contain rounded-xl"
                          />
                        )}
                        <p className="text-[10px] text-slate-400 text-center mt-2">
                          Heatmap reveals exact neural feature activation focus over fungal/bacterial leaf lesions.
                        </p>
                      </div>
                    ) : (
                      <div className="p-3 rounded-2xl bg-muted/40 border border-border/60 text-xs text-muted-foreground flex items-center gap-2">
                        <Info className="w-4 h-4 text-teal-600 shrink-0" />
                        <span>Integrated Vision Diagnostics verified pathology based on lesion clustering and chlorosis morphology.</span>
                      </div>
                    )}
                  </div>

                  {/* Sri Lankan Department of Agriculture Treatment Protocols */}
                  <div className="space-y-3 pt-2">
                    <span className="text-xs font-bold text-foreground flex items-center gap-1.5 uppercase tracking-wider">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      Department of Agriculture (DOA) Prescription
                    </span>

                    {/* Protocol Tabs */}
                    <div className="flex gap-1.5 border-b border-border pb-2">
                      <button
                        type="button"
                        onClick={() => setActiveTab("bio")}
                        className={`text-xs px-3 py-1.5 rounded-xl font-bold transition-all ${activeTab === "bio"
                            ? "bg-emerald-600 text-white shadow-sm"
                            : "bg-muted text-muted-foreground hover:text-foreground"
                          }`}
                      >
                        🌿 Organic & Biological
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveTab("chem")}
                        className={`text-xs px-3 py-1.5 rounded-xl font-bold transition-all ${activeTab === "chem"
                            ? "bg-teal-600 text-white shadow-sm"
                            : "bg-muted text-muted-foreground hover:text-foreground"
                          }`}
                      >
                        🧪 Chemical Control
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveTab("cultural")}
                        className={`text-xs px-3 py-1.5 rounded-xl font-bold transition-all ${activeTab === "cultural"
                            ? "bg-amber-600 text-white shadow-sm"
                            : "bg-muted text-muted-foreground hover:text-foreground"
                          }`}
                      >
                        🚜 Cultural Practices
                      </button>
                    </div>

                    {/* Protocol Content Area */}
                    <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 text-sm leading-relaxed text-foreground">
                      {activeTab === "bio" && (
                        <div className="space-y-2">
                          <div className="font-bold text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Eco-Friendly Bio-Pesticide / Fungicide Management:
                          </div>
                          <p className="text-xs sm:text-sm">
                            {result.treatment_advisory?.biological_control}
                          </p>
                        </div>
                      )}

                      {activeTab === "chem" && (
                        <div className="space-y-2">
                          <div className="font-bold text-teal-800 dark:text-teal-300 text-xs flex items-center gap-1.5">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                            DOA Recommended Chemical Application:
                          </div>
                          <p className="text-xs sm:text-sm">
                            {result.treatment_advisory?.chemical_control}
                          </p>
                        </div>
                      )}

                      {activeTab === "cultural" && (
                        <div className="space-y-2">
                          <div className="font-bold text-amber-800 dark:text-amber-300 text-xs flex items-center gap-1.5">
                            <Sliders className="w-3.5 h-3.5" />
                            Field Agronomy, Spacing & Irrigation:
                          </div>
                          <p className="text-xs sm:text-sm">
                            {result.treatment_advisory?.cultural_practices}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Alternative Class Candidates */}
                  {result.alternatives && result.alternatives.length > 0 && (
                    <div className="pt-2">
                      <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider block mb-2">
                        Alternative Class Probabilities:
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {result.alternatives.map((alt, i) => (
                          <Badge key={i} variant="secondary" className="text-[11px] font-medium py-1 px-2.5">
                            {alt.disease}: {(alt.confidence * 100).toFixed(1)}%
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="border-dashed border-2 border-border/80 p-8 text-center flex flex-col items-center justify-center min-h-[400px] text-muted-foreground space-y-3">
              <div className="w-16 h-16 rounded-3xl bg-teal-500/10 text-teal-600 flex items-center justify-center">
                <Leaf className="w-8 h-8" />
              </div>
              <div className="max-w-sm space-y-1">
                <h4 className="text-base font-bold text-foreground">
                  Ready to Inspect Crop Leaves
                </h4>
                <p className="text-xs text-muted-foreground">
                  Select a leaf photo or tap one of the presets above to generate a full pathological report with Grad-CAM heatmaps.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Historical Diagnostics Gallery */}
      {history.length > 0 && (
        <div className="space-y-3 pt-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-foreground flex items-center gap-2">
              <Clock className="w-4 h-4 text-teal-600" />
              Past Leaf Scans & Diagnoses ({history.length})
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {history.map((item, idx) => (
              <Card
                key={item.id || idx}
                onClick={() => {
                  setResult(item);
                  if (item.image_preview) setPreviewUrl(item.image_preview);
                }}
                className="group cursor-pointer hover:border-teal-500/50 hover:shadow-md transition-all p-3 space-y-2 relative overflow-hidden"
              >
                <div className="flex items-center gap-2">
                  {item.image_preview ? (
                    <img
                      src={item.image_preview}
                      alt={item.crop}
                      className="w-12 h-12 rounded-xl object-cover border border-border shrink-0"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-600 flex items-center justify-center shrink-0">
                      <Leaf className="w-6 h-6" />
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-foreground truncate group-hover:text-teal-600 transition-colors">
                      {item.prediction}
                    </p>
                    <p className="text-[11px] text-muted-foreground flex items-center gap-1">
                      <span>{item.crop || "Crop"}</span>
                      <span>•</span>
                      <span>{item.severity_level || "Moderate"}</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-between text-[10px] text-muted-foreground/80 border-t border-border/50 pt-1.5">
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  <span className="text-teal-600 font-semibold flex items-center gap-0.5">
                    Inspect <ChevronRight className="w-3 h-3" />
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
