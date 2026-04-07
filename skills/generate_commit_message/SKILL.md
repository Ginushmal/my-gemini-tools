---
name: Generate Commit Message
description: Generate a conventional commit message and description from the git diff, optionally using a task ID or description.
---
# Generate Commit Message

When the user asks you to generate a commit message, follow these instructions based on what the user provided:

## 1. Context Gathering
- **If the user provides a `task_id`:** First you need to read the task description of the given `task_id` from the current project in Azure DevOps Server using the `get_work_item_with_attachments` tool. Use the project name provided in the project's GEMINI.md file as `# Project Name : <Project Name>`.
- **If the user provides a `task_description`:** Use the provided description as context.
- **If no task info is provided:** Proceed directly to reviewing the git diff.

## 2. Reading Diffs
**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.

Run the appropriate git commands to get the diff:
- Changed files: `git diff HEAD --name-only`
- Diff content: `git diff HEAD` (only targeting relevant files like `*.java`, `*.sql`, `*.prc`, `*.jsp`, `*.js`, `*.jsx`)

## 3. Generate the Message
Generate a Conventional Commit message and a description for it based on the git diff (and task context if available). 
- The commit message should include `feature :` as a prefix if the task I'm working on is a feature, or `fix :` prefix if it is a bug fix. 
- Ignore the `.md` files in the diff and any files that are in the `.gemini` folder; only consider the changes done to programming files. 
- The description should be concise and point-wise without a hierarchical structure.
- Highlight the main changes made after the last commit, and include all and every change made in the diff. Do not leave anything out. 
- Include what you did and how you did it too in the description. 
- If you are mentioning any file names, class names or method names or anything that is a direct reference from the code or codebase, wrap that word with \`\` (backticks) so when I copy the text, it will be easy to identify them in markdown format.
