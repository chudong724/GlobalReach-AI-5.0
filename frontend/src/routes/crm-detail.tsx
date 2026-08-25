import { useEffect, useState } from "react";
import { useParams } from "@tanstack/react-router";
import { ArrowLeft, BrainCircuit, CalendarClock, Save, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";
const headers = (extra?: HeadersInit) => API_TOKEN ? { ...(extra || {}), "X-API-Key": API_TOKEN } : (extra || {});
async function api(path: string, init?: RequestInit) {
  const r = await fetch(path, { ...init, headers: headers(init?.headers) });
  const text = await r.text(); let data: any = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`); return data;
}

const stages = ["new", "qualified", "contacted", "replied", "negotiating", "won", "lost"];

export function CRMDetailPage() {
  const params = useParams({ strict: false }) as { contactId?: string };
  const id = params.contactId || "";
  const [contact, setContact] = useState<any>(null); const [activities, setActivities] = useState<any[]>([]);
  const [plan, setPlan] = useState<any>(null); const [note, setNote] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);

  const load = async () => { if (!id) return; try { const d = await api(`/api/v1/crm/contacts/${id}`); setContact(d.contact); setActivities(d.activities || []); } catch (e) { setMessage(String(e)); } };
  useEffect(() => { void load(); }, [id]);

  const salesState = async (payload: any) => { setBusy(true); try { await api(`/api/v1/crm/contacts/${id}/sales-state`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) }); setNote(""); await load(); } catch(e){ setMessage(String(e)); } finally { setBusy(false); } };
  const generate = async () => { setBusy(true); setMessage("AI 正在生成销售策略…"); try { const d=await api(`/api/v1/crm/contacts/${id}/ai-sales-plan`,{method:"POST"}); setPlan(d.plan); setMessage("AI 销售计划已生成，并已安排建议跟进日期"); await load(); } catch(e){setMessage(`生成失败：${e}`);} finally{setBusy(false);} };

  if (!contact) return <div className="p-6">{message || "加载客户资料…"}</div>;
  return <div className="space-y-6">
    <div className="flex items-center justify-between"><div><a href="/crm" className="mb-2 flex items-center gap-1 text-sm text-muted-foreground"><ArrowLeft className="h-4 w-4"/>返回 CRM</a><h1 className="text-2xl font-bold">{contact.company_name || contact.email || "客户详情"}</h1><p className="text-sm text-muted-foreground">{contact.contact_name} {contact.job_title ? `· ${contact.job_title}` : ""}</p></div><Button onClick={() => void generate()} disabled={busy}><BrainCircuit className="mr-2 h-4 w-4"/>AI 销售计划</Button></div>
    {message && <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">{message}</div>}

    <div className="grid gap-4 md:grid-cols-3">
      <Card><CardHeader><CardTitle className="text-base">客户评级</CardTitle></CardHeader><CardContent><div className="text-4xl font-bold">{contact.lead_score || 0}</div><div className="mt-2 text-sm">邮箱：{contact.email_verification || "unknown"}</div></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-base">销售阶段</CardTitle></CardHeader><CardContent><select className="h-10 w-full rounded-md border bg-background px-3" value={contact.deal_stage || "new"} onChange={(e)=>void salesState({deal_stage:e.target.value})}>{stages.map(s=><option key={s} value={s}>{s}</option>)}</select></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-base">下次跟进</CardTitle></CardHeader><CardContent><div className="flex items-center gap-2 text-sm"><CalendarClock className="h-4 w-4"/>{contact.next_follow_up_at ? new Date(contact.next_follow_up_at).toLocaleString() : "尚未安排"}</div></CardContent></Card>
    </div>

    <Card><CardHeader><CardTitle className="text-base">客户资料</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-2 text-sm">
      <div><b>邮箱：</b>{contact.email || "—"}</div><div><b>电话：</b>{contact.phone || "—"}</div><div><b>国家：</b>{contact.country || "—"}</div><div><b>网站：</b>{contact.website || "—"}</div><div><b>LinkedIn：</b>{contact.linkedin || "—"}</div><div><b>来源：</b>{contact.source || "—"}</div><div className="md:col-span-2"><b>备注：</b>{contact.notes || "—"}</div>
    </CardContent></Card>

    {plan && <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4"/>AI 销售建议</CardTitle></CardHeader><CardContent className="space-y-4 text-sm">
      <div><b>评级理由：</b>{plan.rating_reason || "—"}</div><div><b>采购需求假设：</b>{plan.buyer_hypothesis || "—"}</div><div><b>下一步：</b>{plan.next_action || "—"}</div><div><b>谈判策略：</b>{Array.isArray(plan.negotiation_strategy) ? plan.negotiation_strategy.join("；") : plan.negotiation_strategy || "—"}</div>
      <div className="rounded-md border p-3"><div className="font-semibold">开发信主题</div><div>{plan.email_subject || "—"}</div><div className="mt-3 font-semibold">开发信正文</div><pre className="mt-1 whitespace-pre-wrap font-sans">{plan.email_body || "—"}</pre></div>
      {Array.isArray(plan.risk_flags) && plan.risk_flags.length>0 && <div><b>风险提示：</b>{plan.risk_flags.join("；")}</div>}
    </CardContent></Card>}

    <Card><CardHeader><CardTitle className="text-base">新增跟进记录</CardTitle></CardHeader><CardContent className="flex gap-2"><Input value={note} onChange={e=>setNote(e.target.value)} placeholder="记录电话、WhatsApp、邮件或会议进展…"/><Button disabled={!note.trim()||busy} onClick={()=>void salesState({mark_contacted:true,note})}><Save className="mr-2 h-4 w-4"/>保存</Button></CardContent></Card>

    <Card><CardHeader><CardTitle className="text-base">客户时间线</CardTitle></CardHeader><CardContent className="space-y-3">{activities.map(a=><div key={a.id} className="border-l-2 pl-3"><div className="text-sm font-medium">{a.content || a.activity_type}</div><div className="text-xs text-muted-foreground">{new Date(a.created_at).toLocaleString()} · {a.activity_type}</div></div>)}{!activities.length&&<div className="text-sm text-muted-foreground">暂无记录</div>}</CardContent></Card>
  </div>;
}
