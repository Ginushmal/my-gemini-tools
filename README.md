# Gemini CLI Tools & Workflows Guide

This repository contains a comprehensive toolset tailored for the Gemini CLI agent. It utilizes a dual-layer architecture, combining the high-level reasoning of **Agentic Skills** with the secure execution of a **Model Context Protocol (MCP) Server**.

---

## 🏗️ Architecture: MCP Server vs. Skills

### 1. The MCP Server (`python MCP/`)
The MCP server is a Python application that exposes strictly programmable endpoints to the Gemini agent. 
- **What it does:** It handles all of the heavy lifting that involves API requests, secure authentications, or specific Python library operations (like `requests` or `pandas`).
- **Included Tools:**
  - `get_work_item_with_attachments`: Securely fetches items from Azure DevOps using personal access tokens, downloads files, and processes them.
  - `excel_to_csv_string`: Uses Pandas to parse binary Excel file data into a readable format for the LLM.
- **Why keep these in the MCP?** It keeps your credentials (`YOUR_PAT`) secure in a `.env` file away from the agent's context, and ensures Python dependencies are sandboxed.

### 2. Agentic Skills (`skills/`)
Skills are the "brains" of the workflows. They are Markdown files that instruct Gemini exactly *how* to handle a complex task.
- **What it does:** Organizes multi-step processes. A skill tells Gemini to run a `git diff` in the shell, read the output, pass it to one of your MCP tools, fetch context, and construct a detailed summary or code review.
- **Why use skills?** You don't need strict parameter syntax (e.g., `tool(id=123)`). You just talk naturally to the agent in the CLI, and the skill guides the agent autonomously.

---

## ⚙️ Setup Instructions

### 1. Setting up the MCP Server
1. Navigate into the MCP directory:
   ```bash
   cd "python MCP"
   ```
2. Ensure you have installed the required dependencies:
   ```bash
   pip install pandas requests fastmcp python-dotenv
   ```
3. Create a `.env` file in the `python MCP` folder and add your credentials:
   ```env
   YOUR_PAT=your_azure_devops_personal_access_token_here
   DOWNLOAD_FOLDER=.gemini\attachments
   ```
4. **Register the MCP Server in your Gemini CLI:**
   - Open your Gemini CLI settings file. On Windows, this is usually located at: `C:\Users\<YourUsername>\.gemini\settings.json`. *(If the file doesn't exist, create it).*
   - Find the `"mcpServers"` object inside the JSON file. If it's not there, you can safely add it at the root of the JSON file.
   - Add a configuration telling Gemini how to run your Python file using `fastmcp`. Your `settings.json` should look like this:
     ```json
     {
       "mcpServers": {
         "MyFirstMCPServer": {
           "command": "fastmcp",
           "args": [
             "run",
             "D:\\my-gemini-tools\\python MCP\\server.py"
           ]
         }
       }
     }
     ```
   > 💡 **Important Beginner Tip:** Ensure you change `D:\\my-gemini-tools\\python MCP\\server.py` to the **exact absolute path** of where this folder lives on your computer. Because strings in a `json` file need properly formed paths, remember to use double-backslashes (`\\`) instead of single ones (`\`)!

### 2. Setting up the Skills
1. Locate the `.gemini` profile directory on your machine (e.g., `C:\Users\<YourUsername>\.gemini\`).
2. Inside that directory, make sure a `skills` folder exists.
3. Copy all the folders from `d:\my-gemini-tools\skills\` directly into your `C:\Users\<YourUsername>\.gemini\skills\` directory.

Your folder structure should look something like this:
```
C:\Users\<YourUsername>\.gemini\
└── skills\
    ├── add_day_end_summary\
    │   └── SKILL.md
    ├── code_review\
    │   └── SKILL.md
    ├── generate_commit_message\
    │   └── SKILL.md
    └── read_task_context\
        └── SKILL.md
```

---

## 🚀 Usage Guide

Once your MCP Server is running and your skills are loaded into the Gemini CLI, you can start automating your development workflow seamlessly. Because these are *Agentic Skills*, you just mention the slash command and talk naturally.

> ⌨️ **Important CLI Tip:** When you type a slash command (e.g., `/Read`), the CLI will offer an autocomplete suggestion. **Press `Tab` (or `Right Arrow`)** to accept the suggestion so you can continue typing the rest of your instruction (like a Task ID). If you press `Enter`, it will immediately submit the incomplete command!

### Command Examples:

#### 🔍 Code Review & Verification
Autonomously perform deep code reviews, check logic against Azure DevOps tasks, and review PRs.
- *Check your current uncommitted work against a task:*
  `> /Code-Review-and-Verification for task ID 123`
- *Review a PR between two branches:*
  `> /Code-Review-and-Verification between target branch "main" and source branch "feature-auth" for task ID 123`
- *Review specific commits based on a description:*
  `> /Code-Review-and-Verification please review commit hashes abc1234 def5678 against this task description: "Implement the new login UI"`

#### 📝 Generate Commit Message
Automatically writes Conventional Commits based on your git working directory and corresponding Azure DevOps item.
- *With a Task ID:*
  `> /Generate-Commit-Message using task ID 123`
- *Just read the diff and make a standard commit:*
  `> /Generate-Commit-Message`

#### 📖 Read Task Context
Fetches task details, attachments, and corresponding templates from Notion, to give the AI the complete context needed for the feature.
- *Usage:*
  `> /Read-Task-Context task ID 456`

#### 📅 Add Day End Summary
Analyzes Git logs/diffs for the day and automatically writes a structured Notion page update.
- *For today's work:*
  `> /Add-Day-End-Summary`
- *For a previous date:*
  `> /Add-Day-End-Summary for the date 05-04-2026`
