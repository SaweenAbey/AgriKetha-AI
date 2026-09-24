import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Activity,
  CheckCircle2,
  ShieldAlert,
  HelpCircle,
  BookOpen,
  Leaf,
  Info,
  AlertTriangle,
  Stethoscope,
  Sparkles,
  PhoneCall,
  Check,
} from "lucide-react";

/**
 * Categorize a section header based on keywords across English, Sinhala, and Tamil.
 */
function getSectionStyle(headerText) {
  const text = String(headerText || "").toLowerCase();

  // 1. Assessment / Diagnosis
  if (
    text.includes("assessment") ||
    text.includes("diagnosis") ||
    text.includes("තක්සේරුව") ||
    text.includes("රෝග") ||
    text.includes("மதிப்பீடு") ||
    text.includes("1.")
  ) {
    return {
      icon: <Stethoscope className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />,
      bg: "bg-teal-500/10 border-teal-500/20 text-teal-900 dark:text-teal-200",
      accent: "text-teal-600 dark:text-teal-400",
      border: "border-teal-500/30",
    };
  }

  // 2. Recommended Actions / Treatment
  if (
    text.includes("recommended") ||
    text.includes("action") ||
    text.includes("treatment") ||
    text.includes("නිර්දේශ") ||
    text.includes("ක්‍රියාමාර්ග") ||
    text.includes("பரிந்துரை") ||
    text.includes("2.")
  ) {
    return {
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />,
      bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-900 dark:text-emerald-200",
      accent: "text-emerald-600 dark:text-emerald-400",
      border: "border-emerald-500/30",
    };
  }

  // 3. Safety Precautions / Chemical Handling
  if (
    text.includes("safety") ||
    text.includes("precaution") ||
    text.includes("ආරක්ෂිත") ||
    text.includes("පියවර") ||
    text.includes("பாதுகாப்பு") ||
    text.includes("3.")
  ) {
    return {
      icon: <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />,
      bg: "bg-amber-500/10 border-amber-500/20 text-amber-900 dark:text-amber-200",
      accent: "text-amber-600 dark:text-amber-400",
      border: "border-amber-500/30",
    };
  }

  // 4. Expert Consultation / Contact
  if (
    text.includes("expert") ||
    text.includes("contact") ||
    text.includes("extension") ||
    text.includes("විශේෂඥ") ||
    text.includes("නිලධාරී") ||
    text.includes("நிபுணர்") ||
    text.includes("4.")
  ) {
    return {
      icon: <PhoneCall className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />,
      bg: "bg-blue-500/10 border-blue-500/20 text-blue-900 dark:text-blue-200",
      accent: "text-blue-600 dark:text-blue-400",
      border: "border-blue-500/30",
    };
  }

  // 5. Sources & Citations
  if (
    text.includes("source") ||
    text.includes("citation") ||
    text.includes("මූලාශ්‍ර") ||
    text.includes("ஆதாரங்கள்") ||
    text.includes("5.")
  ) {
    return {
      icon: <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />,
      bg: "bg-indigo-500/10 border-indigo-500/20 text-indigo-900 dark:text-indigo-200",
      accent: "text-indigo-600 dark:text-indigo-400",
      border: "border-indigo-500/30",
    };
  }

  // Default Header
  return {
    icon: <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />,
    bg: "bg-muted/40 border-border text-foreground",
    accent: "text-emerald-600 dark:text-emerald-400",
    border: "border-border",
  };
}

export const AdvisoryMarkdownViewer = ({ content }) => {
  if (!content) {
    return <p className="text-sm text-muted-foreground italic">No advisory details available.</p>;
  }

  return (
    <div className="advisory-report-body space-y-4 text-foreground text-sm sm:text-base leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => {
            const text = React.Children.toArray(children).join("");
            const style = getSectionStyle(text);
            return (
              <div
                className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border mt-6 mb-3 font-extrabold text-base sm:text-lg shadow-sm ${style.bg} ${style.border}`}
              >
                {style.icon}
                <span>{children}</span>
              </div>
            );
          },
          h2: ({ children }) => {
            const text = React.Children.toArray(children).join("");
            const style = getSectionStyle(text);
            return (
              <div
                className={`flex items-center gap-2.5 px-4 py-2 rounded-xl border mt-5 mb-2.5 font-bold text-sm sm:text-base shadow-sm ${style.bg} ${style.border}`}
              >
                {style.icon}
                <span>{children}</span>
              </div>
            );
          },
          h3: ({ children }) => {
            const text = React.Children.toArray(children).join("");
            const style = getSectionStyle(text);
            return (
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border mt-4 mb-2 font-semibold text-xs sm:text-sm ${style.bg} ${style.border}`}
              >
                {style.icon}
                <span>{children}</span>
              </div>
            );
          },
          p: ({ children }) => {
            return <p className="my-2 leading-relaxed text-foreground/90 font-normal">{children}</p>;
          },
          ul: ({ children }) => {
            return <ul className="my-2.5 space-y-2 pl-1 list-none">{children}</ul>;
          },
          ol: ({ children }) => {
            return <ol className="my-2.5 space-y-2 pl-1 list-none">{children}</ol>;
          },
          li: ({ children }) => {
            return (
              <li className="flex items-start gap-2.5 text-xs sm:text-sm text-foreground/90 leading-relaxed group p-2 rounded-lg hover:bg-muted/40 transition-colors">
                <span className="w-5 h-5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Check className="w-3 h-3 stroke-[2.5]" />
                </span>
                <div className="flex-1 space-y-0.5">{children}</div>
              </li>
            );
          },
          strong: ({ children }) => {
            return (
              <strong className="font-bold text-foreground bg-emerald-500/10 dark:bg-emerald-500/20 px-1.5 py-0.5 rounded text-emerald-950 dark:text-emerald-200">
                {children}
              </strong>
            );
          },
          blockquote: ({ children }) => {
            return (
              <div className="my-3 p-3.5 rounded-xl bg-amber-500/10 border-l-4 border-amber-500 text-amber-950 dark:text-amber-200 text-xs sm:text-sm flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div className="space-y-1">{children}</div>
              </div>
            );
          },
          table: ({ children }) => {
            return (
              <div className="overflow-x-auto my-3 rounded-xl border border-border">
                <table className="min-w-full text-xs text-left divide-y divide-border">{children}</table>
              </div>
            );
          },
          thead: ({ children }) => {
            return <thead className="bg-muted/60 font-semibold">{children}</thead>;
          },
          th: ({ children }) => {
            return <th className="p-2.5 text-foreground">{children}</th>;
          },
          td: ({ children }) => {
            return <td className="p-2.5 border-t border-border/50 text-foreground/90">{children}</td>;
          },
          code: ({ children }) => {
            return (
              <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs text-emerald-600 dark:text-emerald-400">
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
