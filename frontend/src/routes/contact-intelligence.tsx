import { useState } from "react";
import { Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";
const authHeaders = (extra?: HeadersInit) => API_TOKEN ? { ...(extra || {}), "X-API-Key": API_TOKEN } : (extra || {});

export function ContactIntelligencePage() {
  const [website, setWebsite] = useState("");
  const [contactName, setContactName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [data, setData] = useState<any>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const discover = async () => {
    setBusy(true); setMessage("正在运行联系人情报瀑布流…");
    try {
      const r = await fetch("/api/v1/contact-intelligence/discover", {
        method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ website, contact_name: contactName, company_name: companyName }),
      });
      const result = await r.json();
      if (!r.ok) throw new Error(result.detail || `HTTP ${r.status}`);
      setData(result); setMessage(`发现 ${result.candidates?.length || 0} 个候选邮箱`);
    } catch (e) { setMessage(`查询失败：${e}`); }
    finally { setBusy(false); }
  };

  return <div className="space-y-6">
    <div><h1 className="flex items-center gap-2 text-2xl font-bold"><Search className="h-6 w-6"/>联系人情报</h1><p className="mt-1 text-sm text-muted-foreground">公司公开页面 → 搜索证据 → Hunter 可选备用 → MX 验证 → 置信度排序。</p></div>
    <Card><CardHeader><CardTitle className="text-base">查找联系人邮箱</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-3">
      <Input placeholder="公司网站，例如 example.com" value={website} onChange={e=>setWebsite(e.target.value)} />
      <Input placeholder="联系人姓名（可选）" value={contactName} onChange={e=>setContactName(e.target.value)} />
      <Input placeholder="公司名称（可选）" value={companyName} onChange={e=>setCompanyName(e.target.value)} />
      <div className="md:col-span-3"><Button disabled={!website.trim() || busy} onClick={()=>void discover()}><Search className="mr-2 h-4 w-4"/>{busy ? "查询中…" : "开始查找"}</Button></div>
    </CardContent></Card>
    {message && <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">{message}</div>}
    {data && <>
      <div className="grid gap-3 md:grid-cols-3"><Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">公司域名</div><div className="font-semibold">{data.domain}</div></CardContent></Card><Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">Hunter 本月成功使用</div><div className="font-semibold">{data.hunter?.monthly_successes || 0} / {data.hunter?.monthly_cap || 50}</div></CardContent></Card><Card><CardContent className="pt-5"><div className="text-sm text-muted-foreground">Hunter 状态</div><div className="font-semibold">{data.hunter?.configured ? "已配置 · 仅备用" : "未配置"}</div></CardContent></Card></div>
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><ShieldCheck className="h-4 w-4"/>候选邮箱</CardTitle></CardHeader><CardContent><div className="overflow-x-auto"><table className="w-full min-w-[900px] text-sm"><thead><tr className="border-b"><th className="p-2 text-left">邮箱</th><th className="p-2 text-left">置信度</th><th className="p-2 text-left">来源</th><th className="p-2 text-left">状态</th><th className="p-2 text-left">MX</th><th className="p-2 text-left">证据</th></tr></thead><tbody>{(data.candidates||[]).map((x:any)=><tr key={x.email} className="border-b"><td className="p-2 font-medium">{x.email}</td><td className="p-2">{x.confidence}%</td><td className="p-2">{x.source_type}</td><td className="p-2">{x.status}</td><td className="p-2">{x.verification?.has_mx ? "有" : "无"}</td><td className="p-2">{(x.source_urls||[]).slice(0,2).map((u:string)=><div key={u}><a href={u} target="_blank" rel="noreferrer" className="text-primary underline">来源</a></div>)}</td></tr>)}</tbody></table>{!(data.candidates||[]).length && <div className="p-8 text-center text-muted-foreground">没有找到可用候选邮箱。</div>}</div><div className="mt-3 text-xs text-muted-foreground">{data.policy_note}</div></CardContent></Card>
    </>}
  </div>;
}
