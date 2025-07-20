# Contributing to Jarvis-agent

🎉 Thank you for your interest in contributing to `jarvis-agent`! 🎉

We're excited to have you on board. To make the process as smooth as possible for everyone, we've put together these guidelines. Following them helps us review and merge your contributions efficiently.

## 📋 Prerequisites

Before you start, make sure you have the following installed:

- **Make**:  [https://formulae.brew.sh/formula/make](https://formulae.brew.sh/formula/make)
- **Python 3.10** 
- **Google Github account**
- **GCP Project agents-stg**
- **Access to Org https://github.com/project-jarvis-google**

## 🚀 Steps to Contribute

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/project-jarvis-google/jarvis-agent.git
    ```

2.  **Install dependencies:**
    ```bash
    cd agent-app
    make install
    ```

3.  **Run the development environment:**
    ```bash
    gcloud auth application-default login
    make dev
    ```
    This command starts both the frontend and backend:
    - Frontend: [http://localhost:5173](http://localhost:5173) (for custom UI)
    - Backend: [http://localhost:8000](http://localhost:8000)
      - Backend Docs: [http://localhost:8000/docs](http://localhost:8000/docs) (FastAPI)
      - ADK UI: [http://localhost:8000/](http://localhost:8000/) (ADK UI)

## ✨ Adding a New Agent

This is the most common way to contribute! Here’s how you can add your own sub-agent to the system.

1.  **Create a feature branch:**
    ```bash
    git checkout -b feat-agent-<feature-name>
    ```
2.  **Copy and modify a sub-agent:** Duplicate the `google_search_dummy_agent` directory in `agent-app/app/sub_agents/`.  Modify the files within the new directory to build your sub-agent.
3.  **Register your sub-agent:**
    - Edit `/Users/arjunvijay/Documents/my-projects/reusable-asset/jarvis/delivery-app-mod-agent/agent-app/app/prompt.py` to add a prompt.
    - Edit `/Users/arjunvijay/Documents/my-projects/reusable-asset/jarvis/delivery-app-mod-agent/agent-app/app/agent.py` to import your sub-agent and include it in the `tools` list within the `root_agent` definition:

```python
      root_agent = LlmAgent(
            name="jarvis_coordinator",
            model=MODEL,
                AgentTool(agent=google_search_dummy_agent),
            ],
        ) 
```
4.  **Documentation:**  Ensure that each method has a proper docstring and follows the project structure.  Also, make sure to add `__init__.py` file in your agent directory.
5.  **Test your changes:**
    1.  Run the following command locally and test your changes for new sub agent by prompting
    ```bash
    make dev
    ```
6.  **Submit a pull request:**  Create a PR and request a review from `@arjunvijaygoogle`. Include screenshots of your local testing in the PR description.
