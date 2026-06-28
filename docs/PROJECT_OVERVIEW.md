# Project Overview

## Vision

TradingOS is an AI-first Trading Operating System that helps traders identify, evaluate, monitor, and improve trading opportunities.

The long-term goal is to build an AI Trading Analyst capable of recommending high-quality trades with supporting evidence, while continuously learning from historical performance. The product evolves through small, incremental, working releases.

## Mission

Build a modular, production-quality AI trading platform using only free and open-source technologies wherever practical. The platform stays provider-agnostic so different AI models, brokers, and market data providers can be swapped without major architectural changes.

## Core Principles

1. Working software over excessive planning.
2. Every sprint ends with a usable feature.
3. Modular architecture.
4. AI assists, but deterministic logic stays testable.
5. Keep the MVP lightweight.
6. Avoid vendor lock-in.
7. Design for extensibility.
8. Documentation is part of the product.
9. Keep infrastructure free during early development.
10. Every module should be replaceable.

## MVP Goal

The first usable version should:

- Receive market events
- Analyze market context
- Produce trade recommendations
- Explain reasoning
- Notify the user
- Store recommendation history

## Target Users

- **Primary:** Retail traders in Indian F&O.
- **Future:** Swing traders, equity traders, multi-market investors.

## Development Philosophy

- Build vertically — each sprint produces a demonstrable feature.
- Avoid building frameworks before they are needed.
- Optimize for execution velocity and reviewability.

## Technology Philosophy

- Free-first.
- Prefer local execution wherever possible.
- Cloud services remain optional.

## AI Philosophy

AI augments trading decisions by:

- ranking opportunities
- explaining reasoning
- identifying risks
- learning from history

The architecture must support multiple AI providers (Ollama, OpenAI, Anthropic, Gemini) selected via configuration alone.

## Definition of Done

A feature is complete when:

- Code builds successfully
- Runs locally
- Has documentation
- Has basic tests
- Has logging
- Is reviewed
- Is ready for the next sprint
