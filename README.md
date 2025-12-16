![Warehouse Drone Management banner](./docs/assets/ChatGPT Image Dec 16,2025, 09_11_24 PM.png)

# Warehouse Drone Management (WDM)
### Drone-Based Warehouse Inventory Scanning System (Prototype)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%7C%20Flask-blue)](#backend)
[![Frontend](https://img.shields.io/badge/frontend-React%20%7C%20Streamlit-blueviolet)](#dashboard-ui)
[![Simulation](https://img.shields.io/badge/drone-sim-Python-orange)](#drone-simulator)

WDM is a simplified, end-to-end prototype of a **drone-based warehouse inventory scanning system**. A drone (simulated first; real drone optional) scans **QR/barcodes** on shelves, sends scan events to a backend API, updates an inventory database, and streams the results to a dashboard in (near) real time.

> This project is designed to break a big “warehouse drone” idea into **achievable, measurable phases** with clear milestones—great for mentorship/internship portfolios and QA automation practice.

---

## Table of Contents
- [What problem does this solve?](#what-problem-does-this-solve)
- [Key Features](#key-features)
- [High-Level Architecture](#high-level-architecture)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Drone Simulator](#drone-simulator)
- [Backend](#backend)
- [Dashboard UI](#dashboard-ui)
- [API Contract](#api-contract)
- [Testing & QA](#testing--qa)
- [Roadmap (Phases & Milestones)](#roadmap-phases--milestones)
- [Docs & Diagrams](#docs--diagrams)
- [Contributing](#contributing)
- [License](#license)

---

## What problem does this solve?
Manual cycle-counting and inventory audits are time-consuming and error-prone. WDM demonstrates how **autonomous scanning** (or a realistic simulator) can:
- capture item IDs (SKU/serial) from QR/barcodes,
- attach a timestamp and warehouse location,
- persist scan history,
- visualize inventory and drone/system status in a dashboard.

---

## Key Features
- 🛸 **Drone (simulated) warehouse navigation** on a grid of aisles/shelves
- 📷 **QR/barcode scanning** (from images or generated codes)
- 🔌 **REST API ingestion** of scan events (`POST /scan-item`)
- 🗄️ **Inventory database** (SQLite for dev, Postgres optional)
- 📊 **Dashboard** showing:
  - scanned items feed
  - inventory list
  - basic warehouse map/grid
  - drone online/offline + last-seen heartbeat
- ✨ **Optional AI summary** (e.g., “Aisle 5 scanned; 2 missing SKUs detected…”)
- ✅ **QA-first deliverables**: test plan, test cases, Postman collection, automated API/UI tests

---

## High-Level Architecture

```mermaid
flowchart LR
  D[Drone / Simulator] -->|JSON scan events| API[Backend API]
  API --> DB[(Inventory DB)]
  API -->|SSE/WebSocket or polling| UI[Dashboard]
  API -->|optional| AI[AI Summary Module]
  AI --> UI
