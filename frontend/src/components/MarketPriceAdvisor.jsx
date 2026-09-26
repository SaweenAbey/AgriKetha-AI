import React, { useEffect, useMemo, useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Search,
  ExternalLink,
  CalendarDays,
  Loader2,
  AlertCircle,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useLanguage } from "@/context/LanguageContext";
import { marketService } from "@/services/api";

const CATEGORIES = ["Vegetables", "Other", "Fruits", "Rice", "Fish"];

const todayInSriLanka = () =>
  new Date(Date.now() + 5.5 * 60 * 60 * 1000).toISOString().slice(0, 10);

const formatPrice = (value) =>
  value == null ? null : value.toLocaleString("en-LK", { minimumFractionDigits: 0, maximumFractionDigits: 2 });

const ChangeChip = ({ pct }) => {
  if (pct == null) return null;
  if (pct === 0) {
    return (
      <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-muted-foreground">
        <Minus className="w-3 h-3" /> 0%
      </span>
    );
  }
  const up = pct > 0;
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-[10px] font-bold px-1.5 py-0.5 rounded-md ${
        up
          ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
          : "bg-rose-500/10 text-rose-700 dark:text-rose-300"
      }`}
    >
      {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {up ? "+" : ""}
      {pct}%
    </span>
  );
};

const MoversCard = ({ title, items, icon: Icon, tone }) => (
  <Card className="border-border/80">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm flex items-center gap-2">
        <Icon className={`w-4 h-4 ${tone}`} />
        {title}
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-2">
      {items.map((m) => (
        <div key={`${m.name}-${m.market}`} className="flex items-center justify-between gap-2 text-xs">
          <div className="min-w-0">
            <p className="font-semibold text-foreground truncate">{m.name}</p>
            <p className="text-[10px] text-muted-foreground">
              {m.market} · Rs. {formatPrice(m.yesterday)} → Rs. {formatPrice(m.today)}
            </p>
          </div>
          <ChangeChip pct={m.change_pct} />
        </div>
      ))}
    </CardContent>
  </Card>
);

export const MarketPriceAdvisor = () => {
  const { t } = useLanguage();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [category, setCategory] = useState("Vegetables");
  const [priceType, setPriceType] = useState("wholesale");
  const [query, setQuery] = useState("");

  const loadPrices = async () => {
    setLoading(true);
    setError("");
    try {
      setReport(await marketService.getPrices());
    } catch (err) {
      setError(err.response?.data?.detail || t("marketError"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrices();
  }, []);

  const filteredItems = useMemo(() => {
    if (!report) return [];
    const q = query.trim().toLowerCase();
    return report.items.filter(
      (item) =>
        (category === "All" || item.category === category) &&
        (!q || item.name.toLowerCase().includes(q)) &&
        item.prices.some((p) => p.type === priceType)
    );
  }, [report, category, priceType, query]);

  const markets = useMemo(() => {
    const seen = [];
    filteredItems.forEach((item) =>
      item.prices.forEach((p) => {
        if (p.type === priceType && !seen.includes(p.market)) seen.push(p.market);
      })
    );
    return seen;
  }, [filteredItems, priceType]);

  const movers = useMemo(() => {
    if (!report) return { up: [], down: [] };
    const all = report.items
      .filter((item) => item.category !== "Fish")
      .flatMap((item) =>
        item.prices
          .filter((p) => p.type === "wholesale" && p.change_pct != null && p.change_pct !== 0)
          .map((p) => ({ name: item.name, ...p }))
      );
    return {
      up: all.filter((m) => m.change_pct > 0).sort((a, b) => b.change_pct - a.change_pct).slice(0, 4),
      down: all.filter((m) => m.change_pct < 0).sort((a, b) => a.change_pct - b.change_pct).slice(0, 4),
    };
  }, [report]);

  if (loading && !report) {
    return (
      <Card className="p-10 flex flex-col items-center gap-3 border-amber-500/30 bg-amber-500/5">
        <Loader2 className="w-7 h-7 text-amber-600 animate-spin" />
        <p className="text-xs text-muted-foreground">{t("marketLoading")}</p>
      </Card>
    );
  }

  if (error && !report) {
    return (
      <Card className="p-8 flex flex-col items-center gap-3 text-center border-rose-500/30 bg-rose-500/5">
        <AlertCircle className="w-7 h-7 text-rose-600" />
        <p className="text-sm text-foreground">{error}</p>
        <Button size="sm" variant="outline" onClick={loadPrices} className="gap-1.5 text-xs rounded-xl">
          <RefreshCw className="w-3.5 h-3.5" /> {t("marketRefresh")}
        </Button>
      </Card>
    );
  }

  const isToday = report.report_date === todayInSriLanka();
  const reportDateLabel = new Date(`${report.report_date}T00:00:00`).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent">
        <CardHeader className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 space-y-0">
          <div className="flex items-start gap-3">
            <div className="w-11 h-11 shrink-0 rounded-2xl bg-amber-500/15 text-amber-600 flex items-center justify-center">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-lg">{t("marketCenterTitle")}</CardTitle>
              <CardDescription className="text-xs max-w-2xl">{t("marketCenterDesc")}</CardDescription>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <Badge className="bg-amber-600 hover:bg-amber-600 text-white gap-1 text-[11px]">
              <CalendarDays className="w-3 h-3" /> {t("marketReportDate")}: {reportDateLabel}
            </Badge>
            <Button
              size="sm"
              variant="outline"
              onClick={loadPrices}
              disabled={loading}
              className="gap-1.5 text-xs rounded-xl"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              {t("marketRefresh")}
            </Button>
          </div>
        </CardHeader>
        {!isToday && (
          <CardContent className="pt-0">
            <p className="flex items-center gap-1.5 text-[11px] text-amber-800 dark:text-amber-300">
              <Info className="w-3.5 h-3.5 shrink-0" />
              {t("marketNotToday")}
            </p>
          </CardContent>
        )}
      </Card>

      {/* Top movers */}
      {(movers.up.length > 0 || movers.down.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MoversCard title={t("marketTopRisers")} items={movers.up} icon={TrendingUp} tone="text-emerald-600" />
          <MoversCard title={t("marketTopFallers")} items={movers.down} icon={TrendingDown} tone="text-rose-600" />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {["All", ...CATEGORIES].map((c) => (
            <Button
              key={c}
              size="sm"
              variant={category === c ? "default" : "outline"}
              onClick={() => setCategory(c)}
              className={`rounded-xl text-xs h-8 ${category === c ? "bg-amber-600 hover:bg-amber-700 text-white" : ""}`}
            >
              {c === "All" ? t("marketAll") : t(`marketCat${c}`)}
            </Button>
          ))}
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="inline-flex rounded-xl border border-border p-0.5 bg-card">
            {["wholesale", "retail"].map((type) => (
              <button
                key={type}
                onClick={() => setPriceType(type)}
                className={`flex-1 px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  priceType === type ? "bg-amber-600 text-white" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {type === "wholesale" ? t("marketWholesale") : t("marketRetail")}
              </button>
            ))}
          </div>
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("marketSearch")}
              className="pl-8 h-9 text-xs rounded-xl sm:w-56"
            />
          </div>
        </div>
      </div>

      {/* Price table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-muted/50 border-b border-border text-left">
                <th className="px-4 py-3 font-semibold text-foreground sticky left-0 bg-muted/90 backdrop-blur-sm">
                  {t("marketItem")}
                </th>
                {markets.map((m) => (
                  <th key={m} className="px-4 py-3 font-semibold text-foreground text-right whitespace-nowrap">
                    {m}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => {
                const byMarket = Object.fromEntries(
                  item.prices.filter((p) => p.type === priceType).map((p) => [p.market, p])
                );
                return (
                  <tr key={`${item.category}-${item.name}`} className="border-b border-border/60 hover:bg-muted/30">
                    <td className="px-4 py-2.5 sticky left-0 bg-card">
                      <p className="font-semibold text-foreground whitespace-nowrap">{item.name}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {item.unit}
                        {category === "All" && ` · ${t(`marketCat${item.category}`)}`}
                      </p>
                    </td>
                    {markets.map((m) => {
                      const p = byMarket[m];
                      return (
                        <td key={m} className="px-4 py-2.5 text-right whitespace-nowrap">
                          {p && p.today != null ? (
                            <div className="flex flex-col items-end gap-0.5">
                              <span className="font-bold text-sm text-foreground">Rs. {formatPrice(p.today)}</span>
                              <div className="flex items-center gap-1.5">
                                {p.yesterday != null && (
                                  <span
                                    className="text-[10px] text-muted-foreground"
                                    title={t("marketYesterday")}
                                  >
                                    {formatPrice(p.yesterday)}
                                  </span>
                                )}
                                <ChangeChip pct={p.change_pct} />
                              </div>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">{t("marketNa")}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredItems.length === 0 && (
            <p className="p-6 text-center text-xs text-muted-foreground">{t("marketNoResults")}</p>
          )}
        </div>
      </Card>

      {/* Source */}
      <p className="text-[11px] text-muted-foreground flex flex-wrap items-center gap-1">
        {t("marketSource")}: {report.source}
        <a
          href={report.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-0.5 text-amber-700 dark:text-amber-400 hover:underline font-medium"
        >
          PDF <ExternalLink className="w-3 h-3" />
        </a>
        · {t("marketYesterday")} → {t("marketToday")} ({t("marketChange")} %)
      </p>
    </div>
  );
};
