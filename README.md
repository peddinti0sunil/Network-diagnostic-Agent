# NetScanAI — AI-Powered Network Diagnostic Agent

A local AI agent built with LangGraph that diagnoses network issues using real tools.
Ask it anything about a host or domain — it figures out what to scan, runs the tools,
and gives you a structured report with healthy / warnings / critical categories.

Built with: **LangChain + LangGraph + Groq (free) + Llama 3.3 70b + Python**

---

## What it does

You type: `"Diagnose scanme.nmap.org"`

The agent:
1. Pings the host to check reachability
2. Scans common TCP ports (HTTP, HTTPS, SSH, FTP, MySQL, RDP)
3. Does a DNS lookup and resolves all IPs
4. Checks the website status and response time
5. Runs a deep nmap scan for service and version detection
6. Generates a structured report — healthy, warnings, critical, recommendation

All of this automatically. No manual commands.

---

## Project structure

```
NetScanAI/
├── agent.py          ← LangGraph agent: state, nodes, graph, memory, main loop
├── tools.py          ← 6 network tools the agent can call
├── requirements.txt  ← Python dependencies
├── .env              ← Your API key (create this yourself, never commit)
├── .gitignore        ← Keeps .env and agent_memory.db out of git
└── README.md         ← This file
```

---

## Prerequisites

- Python 3.10 or newer
- nmap installed on your OS (for the nmap_scan tool)
- A free Groq API key

**Install nmap:**
```bash
# Windows — download installer from:
https://nmap.org/download.html

# Linux
sudo apt install nmap

# Mac
brew install nmap
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/peddinti0sunil/Network-diagnostic-Agent
cd Network-diagnostic-Agent
```


### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get a free Groq API key
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up — free, no credit card needed
3. Create an API key and copy it

### 5. Create your .env file
Create a file named `.env` in the project root:
```
GROQ_API_KEY=gsk_your_key_here
```

Never commit this file. It is already in .gitignore.

### 6. Run the agent
```bash
python agent.py
```

---

## Example session

```
Enter query or [exit]: Diagnose google.com

=== NETWORK DIAGNOSTIC REPORT ===
Target: google.com

HEALTHY
  • Host is reachable (avg 14ms latency)
  • Port 80/HTTP is open
  • Port 443/HTTPS is open
  • DNS resolves to 4 IPs
  • Website returns 200 OK in 182ms

WARNINGS
  None

CRITICAL
  None

RECOMMENDATION
  google.com is fully healthy. No action needed.
```

---

## The 6 tools

| Tool | What it does |
|------|-------------|
| `ping_host` | Sends 4 ICMP packets, checks reachability and latency |
| `scan_port` | Checks 6 common TCP ports (HTTP, HTTPS, SSH, FTP, MySQL, RDP) |
| `dns_lookup` | Resolves domain to all IP addresses using socket |
| `check_website` | HTTP GET request, returns status code and response time |
| `nmap_scan` | Deep port scan with service and version detection |
| `shell_tool` | Runs whitelisted shell commands (ping, nslookup, tracert, netstat, ipconfig) |

---

## Architecture

```
User input
    ↓
[llm_node] ← ← ← ← ← ← ← ← ← +
    ↓ tools_condition             |
    ├── has tool_calls? → [ToolNode] → +
    └── no tool_calls?  → [report_node]
                              ↓
                            [END]
```

The agent runs the **ReAct loop** (Reason → Act → Observe → repeat) until it
has enough information, then generates a structured `DiagnosticReport` using
Pydantic + `with_structured_output`.

Memory is persisted across sessions using `SqliteSaver` — the agent remembers
previous conversations when you restart it.

---

## Security notes

**This tool is for personal/educational use on your own network.**

Built-in protections:
- `shell_tool` only allows whitelisted commands (ping, nslookup, tracert, netstat, ipconfig)
- Command chaining characters are blocked (`&`, `|`, `;`, `>`, `<`, `` ` ``)
- Website content is never passed to the LLM (protects against prompt injection)

---

## .gitignore

Make sure your repo has this `.gitignore` before your first commit:

```
.env
agent_memory.db
__pycache__/
*.pyc
*.pyo
venv/
```

---

## Tech stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Agent runtime | LangGraph | StateGraph, nodes, edges, ReAct loop |
| LLM | Groq + Llama 3.3 70b | Free, fast inference |
| Messages | LangChain Core | HumanMessage, AIMessage, ToolMessage, SystemMessage |
| Tools | LangChain Core @tool | ping, port scan, DNS, HTTP, nmap, shell |
| Structured output | Pydantic BaseModel | DiagnosticReport validation |
| Memory | SqliteSaver | Persistent conversation history |
| HTTP client | httpx | Website health checks |
| Port scanning | socket | TCP connect_ex() |
| Deep scanning | python-nmap | Service and version detection |

---

## What I learned building this

This project was built as a learning exercise covering:

- How AI agents work (ReAct loop: Reason → Act → Observe → repeat)
- LangGraph: StateGraph, nodes, edges, conditional routing, checkpointers
- LangChain: message types, tool binding, structured output
- Why `Annotated[list[AnyMessage], operator.add]` matters for state
- The difference between `llm` and `LLM` (base vs tool-bound)
- How `SqliteSaver` enables persistent memory across restarts
- Security: prompt injection, command injection, API key management

---

## License

MIT — do whatever you want with it.
