"""Branded FastAPI entry point for 文美全球AI获客系统."""

from api.app import app

app.title = "文美全球AI获客系统 API"
app.description = "面向外贸与 B2B 场景的 AI 客户开发、CRM、联系人情报、企业知识库、销售运营、商业智能、邮件跟进与回信闭环 API"
app.version = "1.6.0"
