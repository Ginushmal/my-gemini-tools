---
name: Read Task Context
description: Read the task description, attachments, and related project notes to build full context for a given task.
---

# Read Task Context

Whenever the user asks you to read the context for a task (providing a `task_id`), perform the following steps:

1. First you need to read the task description of the given `task_id` from the current project in Azure DevOps Server using the `get_work_item_with_attachments` tool. Use the project name provided in the project's GEMINI.md file as `# Project Name : <Project Name>`.
2. Read all the attachments. If there are any excel files among the attachments, convert them to csv format for your readability using the `excel_to_csv_string` tool.
3. Then you need to read the documentations I have written that is related to this task or this task type.
4. You need to use `notionMCP` to read these documents in the current project's 'Notion Page' which is provided in the projects GEMINI.md file as `# Notion Page : <Notion Page URL>`
   - This page will contain a page named 'Project Notes'.
   - Read that page using the `notion-fetch` tool of `notionMCP`.
   - In that page, there will be a section named 'Task Notes', and under that topic, there will be several notes relating to different types of tasks. You need to decide what note matches the type of the current task based on the info you got from the task description and attachments.
   - Read that specific note using the `notion-fetch` tool of `notionMCP`.
     ( Or check out the .md files that are in the root folder , they have the same information as the notion pages)
5. Combine all the info you got from the task description, attachments and the note to get the full context of the task.
6. Most of the time under the task types note, there will be a section describing the steps to be followed to complete that type of task. Understand that process well, also dive in to any and every related implementation files related to the current task or related processes to understand the implementation process, architecture and the structure.
7. Finally, give me a summary of the complete description of the task and the steps to be followed to complete it.
