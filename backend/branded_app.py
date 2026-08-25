"""Branded FastAPI entry point for 文美全球AI获客系统."""

from api.app import app

app.title = "文美全球AI获客系统 API"
app.description = "面向外贸与 B2B 场景的 AI 客户开发、线索挖掘、CRM、销售策略与自动跟进 API"
app.version = "1.2.0"
