Security & Malware Protection Protocol
📌 Purpose
This document establishes mandatory security guardrails for Cline while building the HubSpot Air Traffic Controller prototype. Because you have access to execute terminal commands, manage file structures, and write code in this environment, you must actively protect this project from malicious packages, unauthorized data exposure, and harmful shell injections.

🛡️ Core Security Directives
1. Package & Dependency Scanning
Before running any installation commands (e.g., pip install, npm install), you must verify that the packages are safe, official, and free of typosquatting malware.

Verify Library Legitimacy: Only download established, official libraries (streamlit, openai, requests, python-dotenv). Do not install unverified or obscure third-party wrappers.

Scan before Install: If adding new dependencies to requirements.txt, perform a quick security baseline verification. Use tools like pip-audit if available in the environment to check for known vulnerabilities.

Version Pinning: Always pin package versions in requirements.txt to prevent malicious upstream dependency updates from corrupting the local environment.

2. Malicious Command & Script Prevention
You are strictly prohibited from downloading or running unverified bash scripts, curl-to-sh commands, or binary executables from external, non-official repositories.

Inspect External Code: If copying utility code or snippets from an external resource, you must inspect the raw text for hidden obfuscation, base64-encoded strings, or unexpected outbound network calls before writing it to a file.

Command Sanitization: Never execute shell commands that bypass standard security logging, attempt to alter system-level permissions (sudo chmod 777), or spawn reverse-shell connections.

No Arbitrary Downloads: Do not use wget or curl to pull files directly into the repository unless the source is explicitly verified as safe (e.g., official HubSpot or OpenAI documentation assets).

3. API Key & Data Leakage Protection
This project interfaces with live API endpoints using highly sensitive tokens. You must prevent credential theft.

Strict .gitignore Enforcement: Ensure that .env is explicitly listed in your .gitignore file before saving any real API keys or tokens. Never commit keys to version control.

Memory Guarding: Do not log raw API tokens, authorization headers, or private customer data fetched from HubSpot to the terminal standard output or to unencrypted local debug log files.

Sandbox Isolation: Ensure all write operations or destructive test requests remain strictly targeted at the HubSpot Sandbox environment token, preventing accidental pollution of Deriv production data.

🚨 Incident Response & Override Rules
If you detect a suspected typo, an insecure third-party code sample, or an absolute requirement to execute a potentially risky terminal command, you must halt progress immediately and present the exact risk clearly to the user for explicit human approval before proceeding.
