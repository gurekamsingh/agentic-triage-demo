# Agentic-Triage-demo


Automatically triages GitHub issues using Claude. When an issue is opened, the agent:
- Searches for duplicate issues
- Reads the source code to find the relevant lines
- Adds the appropriate label
- Posts a comment with a direct link to the buggy code and a suggested fix

---

## Setup

### 1. Add your Anthropic API key

Go to your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | Your key from console.anthropic.com |

`GITHUB_TOKEN` is provided by GitHub automatically — nothing to add.

### 2. Create labels

Go to your repo → **Issues → Labels** and create these:

`bug` `enhancement` `question` `needs-info` `security` `duplicate` `wontfix`

### 3. Push the code

Make sure your repo contains:
```
.github/workflows/triage.yml
agent/triage.py
```

The workflow fires automatically on every new issue — no manual steps needed after this.

---

## Usage

Just open an issue. The agent handles the rest.

Check the **Actions tab** in your repo to watch the agent's reasoning in real time.

Finally you will see a comment under the issue pointing out to exact issue in the code:

<img width="1549" height="874" alt="image" src="https://github.com/user-attachments/assets/db468879-985f-44f8-a50a-a3b2d97ed331" />


---

## Project structure

```
├── main.py                        ← FastAPI app
├── templates/index.html           ← Web UI
├── requirements.txt
├── agent/triage.py                ← Claude agent loop
└── .github/workflows/triage.yml  ← GitHub Actions trigger
```

---

## Run the app locally

```bash
python -m venv venv
source venv/Scripts/activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000
