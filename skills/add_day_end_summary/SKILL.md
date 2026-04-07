---
name: Add Day End Summary
description: Generate and upload a daily summary of all changes made to the project.
---
# Add Day End Summary

When the user asks to add a day end summary (they may or may not provide an `input_date`, if not, use today's date formatted as `DD-MM-YYYY`), perform the following:

**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.

1. Use the git commands to get all the diffs I have made to the current project on the specific date, and all the commits I have made on that date (and their changes).
   Make sure to only consider the .java and .jsp file updates and ignore all other file types.
2. Get all the logs for that date using a command like:
   `git log --since="yyyy-mm-dd" --until="yyyy-mm-dd" --oneline` (adjust date range as needed)
3. Get the diff files and content using:
   `git diff HEAD --name-only`
   `git diff HEAD`
4. Give me a summary of all the changes I have made on that day in the current project.
5. Add that summary into a new page in the Notion page named 'Daily Tasks Done' at `https://www.notion.so/2324ddbb83a98008977fc48e36f20f45?v=2324ddbb83a980af8786000c7c085e26` using `notionMCP`. (Only update if a page already exists for that date).
6. Before adding the new page, read at least 3 of the previously created pages to get an idea about what to write in the new page. Then create a similar structured page for the today's summary.
