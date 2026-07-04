# TradingOS - Project Memory

## Product Vision

TradingOS is an AI-powered decision support system for Indian F&O traders.

Its primary objective is to answer:

> What should I trade today, why should I trade it, what is my risk, and what should I do next?

TradingOS is NOT:

- a charting platform
- a broker
- a portfolio tracker
- another TradingView clone

It consumes market information and produces actionable trading intelligence.

---

## MVP Scope

The MVP will:

- Receive market events
- Analyse them
- Generate recommendations
- Explain reasoning
- Track trade lifecycle
- Maintain trading memory

---

## Product Philosophy

Simple.

Fast.

Explainable.

Opinionated.

Every recommendation must include reasoning.

---

## Architecture Principles

FastAPI Backend

SQLite (MVP)

Provider Pattern for AI

Repository Pattern

Service Layer

Feature-first development

Docker First

GitHub Source of Truth

---

## Public Market Event Schema

{
    "symbol": "",
    "exchange": "",
    "signal": "",
    "price": 0,
    "timeframe": "",
    "strategy": "",
    "timestamp": ""
}

Never expose TradingView-specific fields like:

ticker

action

---

## Long-term AI Providers

Mock

↓

Ollama

↓

OpenAI

↓

Claude

↓

Gemini

↓

Custom Models

No business logic should depend on one provider.