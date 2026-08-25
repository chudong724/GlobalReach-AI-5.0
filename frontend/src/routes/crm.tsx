import { useEffect, useMemo, useState } from "react";
import { Download, FileDown, Plus, RefreshCw, Search, Trash2, Upload, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type CRMContact = {
  id: string;
  company_name: string;
  contact_name: string;
  job_title: string;
  email: string;
  phone: string;
  website: string;
  country: string;
  city: string;
  linkedin: string;
  source: string;
  status: string;
  priority: string;
  notes: string;
};

const emptyContact: Omit<CRMContact, "id"> = {
  company_name: "", contact_name: "", job_title: "", email: "", phone: "",
  website: "", country: "", city: "", linkedin: "", source: "manual",
  status: "new", priority: "normal", notes: "",
};

async function apiJson(path: string, init?: RequestInit) {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error(await response.text() || `HTTP ${response.status}`);
  return response.json();
}

export function CRMPage() {
  const [items, setItems] = useState<CRMContact[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [draft, setDraft] = useState(emptyContact);
  const [showAdd, setShowAdd] = useState(false);

  const load = async () => {
    setLoading(true);
    setMessage("");
    try {
      const data = await apiJson(`/api/v1/crm/contacts?search=${encodeURIComponent(search)}&limit=2000`);
      setItems(data.items || []);
      setSelected(new Set());
    } catch (e) {
      setMessage(`加载失败：${e instanceof Error ? e.message : String(e)}`);
    } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);

  const allChecked = useMemo(() => items.length > 0 && items.every((x) => selected.has(x.id)), [items, selected]);

  const toggleAll = () => setSelected(allChecked ? new Set() : new Set(items.map((x) => x.id)));
  const toggleOne = (id: string) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const deleteSelected = async () => {
    if (!selected.size) return;
    if (!window.confirm(`确认删除选中的 ${selected.size} 个客户吗？`)) return;
    try {
      const data = await apiJson("/api/v1/crm/contacts/delete-many", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: Array.from(selected) }),
      });
      setMessage(`已删除 ${data.deleted ?? 0} 个客户`);
      await load();
    } catch (e) { setMessage(`删除失败：${e instanceof Error ? e.message : String(e)}`); }
  };

  const addContact = async () => {
    try {
      await apiJson("/api/v1/crm/contacts", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft),
      });
      setDraft(emptyContact); setShowAdd(false); setMessage("客户已保存"); await load();
    } catch (e) { setMessage(`保存失败：${e instanceof Error ? e.message : String(e)}`); }
  };

  const importCsv = async (file?: File) => {
    if (!file) return;
    const form = new FormData(); form.append("file", file);
    try {
      const data = await apiJson("/api/v1/crm/import", { method: "POST", body: form });
      setMessage(`导入完成：${data.imported ?? 0} 条，跳过 ${data.skipped ?? 0} 条`); await load();
    } catch (e) { setMessage(`导入失败：${e instanceof Error ? e.message : String(e)}`); }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold"><Users className="h-6 w-6" />客户 CRM</h1>
          <p className="mt-1 text-sm text-muted-foreground">统一管理搜索获得、CSV 导入和人工添加的 B2B 客户资料。</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => window.location.assign("/api/v1/crm/template")}><FileDown className="mr-2 h-4 w-4" />下载导入模板</Button>
          <label className="inline-flex cursor-pointer items-center rounded-md border px-3 py-2 text-sm font-medium hover:bg-accent">
            <Upload className="mr-2 h-4 w-4" />导入 CSV
            <input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => void importCsv(e.target.files?.[0])} />
          </label>
          <Button variant="outline" onClick={() => window.location.assign("/api/v1/crm/export")}><Download className="mr-2 h-4 w-4" />导出全部</Button>
          <Button onClick={() => setShowAdd(!showAdd)}><Plus className="mr-2 h-4 w-4" />新增客户</Button>
        </div>
      </div>

      {showAdd && <Card><CardHeader><CardTitle className="text-base">新增客户</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-3">
        {(["company_name","contact_name","job_title","email","phone","website","country","city","linkedin","source"] as const).map((key) =>
          <Input key={key} placeholder={{company_name:"公司名称",contact_name:"联系人",job_title:"职位",email:"邮箱",phone:"电话",website:"网站",country:"国家",city:"城市",linkedin:"LinkedIn",source:"来源"}[key]} value={draft[key]} onChange={(e) => setDraft({...draft,[key]:e.target.value})} />
        )}
        <Input placeholder="备注" value={draft.notes} onChange={(e) => setDraft({...draft,notes:e.target.value})} />
        <div className="flex gap-2"><Button onClick={() => void addContact()}>保存</Button><Button variant="outline" onClick={() => setShowAdd(false)}>取消</Button></div>
      </CardContent></Card>}

      <Card>
        <CardContent className="pt-6">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <div className="relative min-w-64 flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input className="pl-9" placeholder="搜索公司、联系人、邮箱、网站或国家" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void load()} /></div>
            <Button variant="outline" onClick={() => void load()}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />刷新</Button>
            <Button variant="destructive" disabled={!selected.size} onClick={() => void deleteSelected()}><Trash2 className="mr-2 h-4 w-4" />批量删除 ({selected.size})</Button>
          </div>
          {message && <div className="mb-4 rounded-md border bg-muted/40 px-3 py-2 text-sm">{message}</div>}
          <div className="overflow-x-auto rounded-md border">
            <table className="w-full min-w-[1100px] text-sm">
              <thead className="bg-muted/50"><tr>
                <th className="p-3 text-left"><input type="checkbox" checked={allChecked} onChange={toggleAll} /></th>
                <th className="p-3 text-left">公司</th><th className="p-3 text-left">联系人</th><th className="p-3 text-left">职位</th><th className="p-3 text-left">邮箱</th><th className="p-3 text-left">电话</th><th className="p-3 text-left">国家/城市</th><th className="p-3 text-left">网站</th><th className="p-3 text-left">来源</th><th className="p-3 text-left">状态</th>
              </tr></thead>
              <tbody>{items.map((x) => <tr key={x.id} className="border-t hover:bg-muted/30">
                <td className="p-3"><input type="checkbox" checked={selected.has(x.id)} onChange={() => toggleOne(x.id)} /></td>
                <td className="p-3 font-medium">{x.company_name || "—"}</td><td className="p-3">{x.contact_name || "—"}</td><td className="p-3">{x.job_title || "—"}</td><td className="p-3">{x.email || "—"}</td><td className="p-3">{x.phone || "—"}</td><td className="p-3">{[x.country,x.city].filter(Boolean).join(" / ") || "—"}</td><td className="p-3">{x.website ? <a className="text-primary underline" href={x.website} target="_blank" rel="noreferrer">打开</a> : "—"}</td><td className="p-3">{x.source || "—"}</td><td className="p-3">{x.status || "new"}</td>
              </tr>)}</tbody>
            </table>
            {!loading && !items.length && <div className="p-10 text-center text-muted-foreground">暂无客户数据。可以下载模板后批量导入，或点击“新增客户”。</div>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
