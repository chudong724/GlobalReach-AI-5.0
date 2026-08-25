import { useEffect, useState } from "react";
import { BrainCircuit, CheckCircle2, Eye, EyeOff, Loader2, Save, TestTube2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const API_TOKEN = import.meta.env.VITE_API_ACCESS_TOKEN?.trim() ?? "";

async function request(path: string, init?: RequestInit) {
  const headers: Record<string, string> = { ...(init?.headers as Record<string, string> || {}) };
  if (API_TOKEN) headers["X-API-Key"] = API_TOKEN;
  const response = await fetch(path, { ...init, headers });
  const text = await response.text();
  let data: any = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data;
}

export function DeepSeekPage() {
  const [apiKey, setApiKey] = useState("");
  const [masked, setMasked] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [defaultModel, setDefaultModel] = useState("deepseek/deepseek-chat");
  const [reasoningModel, setReasoningModel] = useState("deepseek/deepseek-reasoner");
  const [configured, setConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    request("/api/v1/wenmei/deepseek").then((data) => {
      setConfigured(Boolean(data.configured));
      setMasked(data.api_key_masked || "");
      if (String(data.default_model || "").startsWith("deepseek/")) setDefaultModel(data.default_model);
      if (String(data.reasoning_model || "").startsWith("deepseek/")) setReasoningModel(data.reasoning_model);
    }).catch((e) => setMessage(`读取配置失败：${e.message}`));
  }, []);

  const save = async () => {
    setSaving(true); setMessage("");
    try {
      const data = await request("/api/v1/wenmei/deepseek", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey, default_model: defaultModel, reasoning_model: reasoningModel }),
      });
      setConfigured(Boolean(data.configured)); setApiKey("");
      setMessage("DeepSeek 配置已保存并立即生效。重启后也会自动加载。 ");
      const refreshed = await request("/api/v1/wenmei/deepseek"); setMasked(refreshed.api_key_masked || "");
    } catch (e) { setMessage(`保存失败：${e instanceof Error ? e.message : String(e)}`); }
    finally { setSaving(false); }
  };

  const test = async () => {
    setTesting(true); setMessage("");
    try {
      const data = await request("/api/v1/wenmei/deepseek/test", { method: "POST" });
      setMessage(`连接成功：${data.model} → ${data.response}`);
    } catch (e) { setMessage(`连接失败：${e instanceof Error ? e.message : String(e)}`); }
    finally { setTesting(false); }
  };

  return <div className="mx-auto max-w-3xl space-y-6">
    <div><h1 className="flex items-center gap-2 text-2xl font-bold"><BrainCircuit className="h-6 w-6" />DeepSeek 原生配置</h1><p className="mt-1 text-sm text-muted-foreground">文美全球AI获客系统可直接调用 DeepSeek API，无需 OpenRouter 中转。</p></div>
    <Card>
      <CardHeader><CardTitle>DeepSeek API</CardTitle><CardDescription>推荐：普通任务使用 deepseek-chat，复杂 ReAct 决策使用 deepseek-reasoner。</CardDescription></CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-2"><Label>API Key</Label><div className="relative"><Input type={showKey ? "text" : "password"} value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder={configured ? `已配置 ${masked}；留空可保留旧 Key` : "输入 DeepSeek API Key"} className="pr-10 font-mono" /><button type="button" onClick={() => setShowKey(!showKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">{showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div>{configured && <p className="flex items-center gap-1 text-xs text-green-600"><CheckCircle2 className="h-3.5 w-3.5" />当前已配置 DeepSeek Key</p>}</div>
        <div className="space-y-2"><Label>默认模型</Label><Input value={defaultModel} onChange={(e) => setDefaultModel(e.target.value)} className="font-mono" /></div>
        <div className="space-y-2"><Label>推理模型</Label><Input value={reasoningModel} onChange={(e) => setReasoningModel(e.target.value)} className="font-mono" /></div>
        <div className="flex gap-2"><Button onClick={() => void save()} disabled={saving}>{saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}保存并启用</Button><Button variant="outline" onClick={() => void test()} disabled={testing || !configured}>{testing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <TestTube2 className="mr-2 h-4 w-4" />}测试连接</Button></div>
        {message && <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">{message}</div>}
      </CardContent>
    </Card>
    <Card><CardHeader><CardTitle className="text-base">推荐用途</CardTitle></CardHeader><CardContent className="grid gap-3 text-sm md:grid-cols-2"><div className="rounded-md border p-3"><b>deepseek-chat</b><p className="mt-1 text-muted-foreground">客户资料提取、关键词、邮件草稿、内容整理等高频任务。</p></div><div className="rounded-md border p-3"><b>deepseek-reasoner</b><p className="mt-1 text-muted-foreground">复杂客户判断、ReAct 工具决策、策略分析与高价值线索推理。</p></div></CardContent></Card>
  </div>;
}
