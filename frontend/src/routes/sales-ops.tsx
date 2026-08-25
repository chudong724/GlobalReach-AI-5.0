import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Activity, CheckCircle2, Mail, RefreshCw, Reply, Target, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";
const headers = () => API_TOKEN ? { "X-API-Key": API_TOKEN } : {};
async function getJson(path: string) {
  const r = await fetch(path, { headers: headers() });
  if (!r.ok) throw new Error(await r.text() || `HTTP ${r.status}`);
  return r.json();
}

type Contact = { id:string; company_name:string; contact_name:string; email:string; deal_stage:string; lead_score:number; next_follow_up_at:string };
type Task = { type:string; priority:string; reason:string; contact:Contact };

export function SalesOpsPage() {
  const [summary, setSummary] = useState<any>({ crm:{}, email:{} });
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const load = async () => {
    setLoading(true); setMessage("");
    try {
      const [s, w] = await Promise.all([getJson("/api/v1/sales-ops/summary"), getJson("/api/v1/sales-ops/daily-worklist?limit=100")]);
      setSummary(s); setTasks(w.items || []);
    } catch (e) { setMessage(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  const crm = summary.crm || {}; const email = summary.email || {};
  const cards = [
    ["客户总数", crm.total || 0, Target], ["今日/逾期待办", crm.due_follow_ups || 0, Activity],
    ["已联系客户", crm.contacted || 0, Mail], ["已回复客户", crm.replied || 0, Reply],
    ["已成交", crm.won || 0, Trophy], ["待发送邮件", email.pending_messages || 0, Mail],
    ["已发送邮件", email.sent_messages || 0, CheckCircle2], ["运行中序列", email.running_sequences || 0, Activity],
  ] as const;
  return <div className="space-y-6">
    <div className="flex items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">销售运营中心</h1><p className="mt-1 text-sm text-muted-foreground">每天从这里查看销售漏斗、邮件运营状态和最需要处理的客户。</p></div><Button variant="outline" onClick={() => void load()}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />刷新</Button></div>
    {message && <div className="rounded-md border px-3 py-2 text-sm">{message}</div>}
    <div className="grid gap-3 md:grid-cols-4">{cards.map(([label,value,Icon]) => <Card key={label}><CardContent className="pt-5"><div className="flex items-center justify-between"><div><div className="text-sm text-muted-foreground">{label}</div><div className="text-2xl font-bold">{value}</div></div><Icon className="h-5 w-5 text-muted-foreground" /></div></CardContent></Card>)}</div>
    <div className="grid gap-3 md:grid-cols-3">
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">联系率</div><div className="text-2xl font-bold">{crm.contact_rate || 0}%</div></CardContent></Card>
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">回复率</div><div className="text-2xl font-bold">{crm.reply_rate || 0}%</div></CardContent></Card>
      <Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">回复后成交率</div><div className="text-2xl font-bold">{crm.win_rate || 0}%</div></CardContent></Card>
    </div>
    <Card><CardHeader><CardTitle>今日优先工作清单</CardTitle></CardHeader><CardContent>
      <div className="space-y-2">{tasks.map((task, i) => <Link key={`${task.contact.id}-${i}`} to="/crm/$contactId" params={{contactId:task.contact.id}} className="block rounded-md border p-3 hover:bg-muted/40"><div className="flex flex-wrap items-center justify-between gap-2"><div><div className="font-medium">{task.contact.company_name || task.contact.contact_name || task.contact.email || "未命名客户"}</div><div className="text-sm text-muted-foreground">{task.reason}</div></div><div className="text-right text-sm"><div>评分 {task.contact.lead_score || 0}</div><div className="text-muted-foreground">{task.contact.deal_stage || "new"}</div></div></div></Link>)}{!tasks.length && <div className="py-8 text-center text-muted-foreground">目前没有需要优先处理的销售任务。</div>}</div>
    </CardContent></Card>
  </div>;
}
