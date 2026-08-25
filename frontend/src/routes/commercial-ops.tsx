import { useEffect, useState } from "react";
import { Download, RefreshCw, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";
const headers = () => API_TOKEN ? { "X-API-Key": API_TOKEN } : {};

export function CommercialOpsPage() {
  const [forecast, setForecast] = useState<any>(null);
  const [message, setMessage] = useState("");
  const load = async () => {
    try {
      const r = await fetch("/api/v1/commercial-ops/forecast", { headers: headers() });
      if (!r.ok) throw new Error(await r.text());
      setForecast(await r.json());
    } catch (e) { setMessage(`加载失败：${e}`); }
  };
  useEffect(() => { void load(); }, []);
  const backup = async () => {
    setMessage("正在生成备份…");
    try {
      const r = await fetch("/api/v1/commercial-ops/backup", { headers: headers() });
      if (!r.ok) throw new Error(await r.text());
      const blob = await r.blob(); const url = URL.createObjectURL(blob); const a = document.createElement("a");
      a.href = url; a.download = "wenmei-global-ai-backup.zip"; a.click(); URL.revokeObjectURL(url); setMessage("备份已生成");
    } catch (e) { setMessage(`备份失败：${e}`); }
  };
  const stages = forecast?.stage_counts || {};
  return <div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="flex items-center gap-2 text-2xl font-bold"><TrendingUp className="h-6 w-6"/>商业运营</h1><p className="mt-1 text-sm text-muted-foreground">销售预测、经营指标与系统数据备份。</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => void load()}><RefreshCw className="mr-2 h-4 w-4"/>刷新</Button><Button onClick={() => void backup()}><Download className="mr-2 h-4 w-4"/>下载数据备份</Button></div></div>
    {message && <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">{message}</div>}
    <div className="grid gap-3 md:grid-cols-4">
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">加权机会指数</div><div className="text-3xl font-bold">{forecast?.weighted_opportunity_units ?? 0}</div></CardContent></Card>
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">联系率</div><div className="text-3xl font-bold">{forecast?.contact_rate ?? 0}%</div></CardContent></Card>
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">回复率</div><div className="text-3xl font-bold">{forecast?.reply_rate ?? 0}%</div></CardContent></Card>
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">回复后成交率</div><div className="text-3xl font-bold">{forecast?.win_rate ?? 0}%</div></CardContent></Card>
    </div>
    <Card><CardHeader><CardTitle className="text-base">Pipeline 阶段分布</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-7">{["new","qualified","contacted","replied","negotiating","won","lost"].map(s=><div key={s} className="rounded-md border p-3 text-center"><div className="text-xs text-muted-foreground">{s}</div><div className="text-2xl font-bold">{stages[s] || 0}</div></div>)}</CardContent></Card>
    <div className="text-xs text-muted-foreground">预测采用阶段权重形成销售健康指数，不代表收入承诺或财务预测。</div>
  </div>;
}
