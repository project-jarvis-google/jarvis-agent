# Jarvis Agent 🤖

An intelligent, extensible agent orchestrator built on Google Cloud using the Agent Development Kit (ADK).
<p align="center">
  <a href="https://github.com/project-jarvis-google/jarvis-agent/actions/workflows/pr-check.yml">
    <img src="https://github.com/project-jarvis-google/jarvis-agent/actions/workflows/pr-check.yml/badge.svg" alt="PR Build Check">
  </a>
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI%20%7C%20React-green.svg" alt="Framework">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
</p>

---

**Jarvis Agent** is a powerful framework for building a "coordinator" agent that can leverage multiple specialized "sub-agents" as tools. Built using the **Google Agent Development Kit (ADK)**, it provides a robust foundation for creating complex, multi-functional AI agents capable of handling sophisticated tasks by delegating to a suite of specialized tools.

The project comes as a full-stack solution with a FastAPI backend and a React-based frontend, complete with an advanced observability and telemetry system.

## ✨ Key Features

-   **🤖 Extensible Agent Architecture:** Easily add new capabilities by creating and registering new sub-agents. The coordinator pattern allows for sophisticated task delegation and complex workflow orchestration.
-   **🛠️ Built with Google ADK:** Leverages the power and structure of the Agent Development Kit for rapid, scalable, and maintainable agent development.
-   **🚀 Full-Stack Solution:** Comes with a high-performance FastAPI backend and a polished, ready-to-use React-based frontend for immediate agent interaction and visualization of results.
-   **📊 Advanced Observability:** A custom telemetry system integrates with Google Cloud services to provide deep insights into agent execution, ensuring no diagnostic data is ever lost.
-   **⚙️ Simplified Workflow:** A comprehensive `Makefile` streamlines the entire development lifecycle, from installation to running the development server.
-   **💾 Session Persistence:** Optional integration with PostgreSQL/AlloyDB to maintain conversation history across sessions.


