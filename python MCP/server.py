from datetime import date
from fastmcp import FastMCP
import pandas as pd
import requests
import base64
import os

# Load environment variables from a .env file if python-dotenv is available.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Proceed without loading from .env; OS environment variables will still be used.
    pass

mcp = FastMCP(name="MyMCPServer")


@mcp.tool
def excel_to_csv_string(file_path: str) -> str:
    """
    Reads an Excel file (.xlsx, .xls) and converts it to a CSV formatted string. for your readability.
    use this any and every time you want to read an excel file.

    Args:
        file_path: The full path to the Excel file.

    Returns:
        A string containing the data in CSV format.
    """
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(file_path)
        
        # Convert the DataFrame to a CSV string without the index column
        csv_string = df.to_csv(index=False)
        
        return csv_string
    except FileNotFoundError:
        return "Error: The file was not found at the specified path."
    except Exception as e:
        return f"An error occurred: {e}"
    
# Read secrets and config from environment
YOUR_PAT = os.getenv("YOUR_PAT")
# Default preserves existing behavior if env not set
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", ".gemini\\attachments")

@mcp.tool
def get_work_item_with_attachments(project_name: str, item_id: int) -> dict:
    """
    Fetches details and downloads attachments for a work item from Azure DevOps Server.
    """
    collection_url = "http://192.168.25.5/Atrad Collection"
    download_folder =  os.path.join(DOWNLOAD_FOLDER, str(item_id))
    
    # --- Authentication Setup ---
    if not YOUR_PAT:
        return {"error": "Missing YOUR_PAT in environment (.env). Please set YOUR_PAT."}
    credentials = f":{YOUR_PAT}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    # --- Step 1: Get Work Item and Attachment Relations ---
    # Use $expand=relations to get the list of attachments
    relations_url = f"{collection_url}/{project_name}/_apis/wit/workitems/{item_id}?$expand=relations&api-version=7.0"
    
    try:
        response = requests.get(relations_url, headers=headers)
        response.raise_for_status()
        work_item_data = response.json()
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get work item details: {e}"}

    # --- Step 2: Find and Download Attachments ---
    attachments = []
    if "relations" in work_item_data:
        for relation in work_item_data["relations"]:
            # Filter for attachments only
            if relation["rel"] == "AttachedFile":
                try:
                    attachment_url = relation["url"]
                    attachment_name = relation["attributes"]["name"]
                    
                    # Make a new request to download the attachment content
                    attachment_response = requests.get(attachment_url, headers=headers)
                    attachment_response.raise_for_status()
                    
                    # Get the binary content
                    attachment_content = attachment_response.content
                    
                    # Save the attachment to a local folder
                    if not os.path.exists(download_folder):
                        os.makedirs(download_folder)
                    file_path = os.path.join(download_folder, attachment_name)
                    with open(file_path, "wb") as f:
                        f.write(attachment_content)

                    # Add attachment info to our list
                    attachments.append({
                        "fileName": attachment_name,
                        "size": len(attachment_content),
                        "file_path": file_path,
                        # For text files, you could decode and add content here
                        # "content": attachment_content.decode('utf-8', errors='ignore') 
                    })

                except requests.exceptions.RequestException as e:
                    print(f"Warning: Failed to download attachment {relation['attributes']['name']}. Error: {e}")
                except KeyError:
                    print("Warning: Skipping a relation that is not a properly formatted attachment.")


    return {
        "workItem": work_item_data,
        "attachments": attachments
    }

@mcp.prompt
def read_task_context(task_id: str) -> str:
    return (
        f"first you need to read the task description of task id {task_id} from the current project in Azure DevOps Server using 'get_work_item_with_attachments' "
        "tool using the project name provided in the project's GEMINI.md file as '# Project Name : <Project Name>', then read all the attachments. "
        "If there are any excel files among the attachments, convert them to csv format for your readability."
        "then you need to read the documentations i have written taht is related to this task or this task type."
        "you need to use 'notionMCP' to read these documents in the current project's 'Notion Page' which is provided in the projects GEMINI.md file as "
        "'# Notion Page : <Notion Page URL>', this page will contain a page named 'Project Notes'  "
        "read that page using 'notion-fetch' tool of 'notionMCP' and in that page , there will be a section named 'Task Notes' , ands under that topic , there will be a several"
        "notes relating to different different types of tasks. you need to decide what note matches the type of the current taks based on the info u got from the task description and attachments. "
        "then you need to read that note using 'notion-fetch' tool of 'notionMCP' and then you need to combine all the info u got from the task description, attachments and the note to get the full context of the task"
        "most of the time under the task types note , there will be a section describing the steps to be followed to complete that "
        "type of task understand that process well, also dive in to any and every related implementation files related to the current taks or related processes to understand the implementation process, architecture and the structure ."
        "then give me a summery of the complete description of the task and the steps to be followed to complete it. "
    )

@mcp.prompt
def add_day_end_summary(input_date: str) -> str:
    formatted_date = ""
    if input_date is None or input_date.strip() == "":
        today = date.today()
        formatted_date = today.strftime("%d-%m-%Y")
    else:
        formatted_date = input_date
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Use the git commands to get all the diffs i have made to the current project on {formatted_date}, and all the commits i have made on {formatted_date}(and their changes)."
        "make sure to only consider the .java and .jsp file updates and ignore all other file types. " 
        "get all the logs"
        "git log --since=\"yyyy-mm-dd\" --until=\"yyyy-mm-dd\" --oneline"
        "DIFF FILES:\n"
        "!{git diff HEAD --name-only}\n\n"
        "DIFF CONTENT:\n"
        "!{git diff HEAD}\n"
        "then give me a summery of all the changes i have made on that day in the current project. and then add that summery in to a new page in "
        "'https://www.notion.so/2324ddbb83a98008977fc48e36f20f45?v=2324ddbb83a980af8786000c7c085e26' notion page named 'Daily Tasks Done' using 'notionMCP' (only update if a page already exists for that date) "
        "Before adding the new page , read a atleast 3 of the previously created pages to get an idea about what to write in the new page. then create a similar structured page for the today's summery."
    )

COMMON_COMMIT_MSG_PROMPT = (
    "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
    "Please generate a Conventional Commit message and a description for it based on the following git diff. The commit message should include 'feature :' as a prefix if the task I'm working on is a feature, or 'fix :' prefix if it is a bug fix. Ignore the .md files in the diff and any files that are in the .gemini folder; only consider the changes done to *.java , *.sql , *.prc files, *.jsp , *.js , *.jsx like programming files. "
    "The description should be concise and point-wise without a hierarchical structure, highlight the main changes made after the last commit, and include all and every change made in the diff. Do not leave anything out. Include what you did and how you did it too in the description. also is you are mentionaning any file names , class names or methods names or anything that is a direct reference from the code or codebase , wrap that word with `` (backticks) so when i copy the text , it will be easy to identify them in markdown format.\n\n"
    "DIFF FILES:\n"
    "!{git diff HEAD --name-only}\n\n"
    "DIFF CONTENT:\n"
    "!{git diff HEAD [list of file names]}\n"
)

@mcp.prompt
def generate_commit_message() -> str:
    return COMMON_COMMIT_MSG_PROMPT

@mcp.prompt
def generate_commit_message_from_task(task_id: str) -> str:
    return (
        f"first you need to read the task description of task id {task_id} from the current project in Azure DevOps Server using 'get_work_item_with_attachments' "
        "tool using the project name provided in the project's GEMINI.md file as '# Project Name : <Project Name>'."
        f"\n\n{COMMON_COMMIT_MSG_PROMPT}"
    )

@mcp.prompt
def generate_commit_message_from_description(task_description: str) -> str:
    return (
        f"TASK DESCRIPTION:\n{task_description}\n\n"
        "Generate a commit message for the changes below, keeping in mind the above task description.\n\n"
        f"{COMMON_COMMIT_MSG_PROMPT}"
    )

@mcp.prompt
def check_task_completion(task_id: str) -> str:
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Perform a final verification for Item #{task_id}. First, retrieve the item description and requirements using the 'get_work_item_with_attachments' tool.\n"
        "Next, review the list of ALL modified and new files below (including staged, unstaged, and untracked files):\n\n"
        "MODIFIED & NEW FILES:\n"
        # 1. Staged/Unstaged modified files
        "!{git diff HEAD --name-only}\n"
        # 2. Untracked (new) files
        "!{git ls-files --others --exclude-standard}\n\n"
        "From this combined output, filter and select **only** source code files (e.g., .java, .sql ,ect.) related to the project. "
        "Strictly **ignore** build artifacts (like .class, .jar), logs, documents, or IDE configuration files (like .settings, .project, .classpath).\n"
        "For each valid source file you identified:\n"
        "   - If it is modified, read changes using `git diff HEAD <filename>`.\n"
        "   - If it is a NEW (untracked) file, read the whole file content (since it has no diff history yet).\n"
        "Compare the code implementation in these files against the requirements of Item #{task_id} and provide a comprehensive review and task completion verification adhering to the following guidelines:\n\n"
        f"{COMMON_REVIEW_PROMPT}"
    )

@mcp.prompt
def check_task_completion_with_description(task_description: str) -> str:
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Perform a final verification for the following task:\n\n"
        f"TASK DESCRIPTION:\n{task_description}\n\n"
        "Review the list of ALL modified and new files below (including staged, unstaged, and untracked files):\n\n"
        "MODIFIED & NEW FILES:\n"
        # 1. Staged/Unstaged modified files
        "!{git diff HEAD --name-only}\n"
        # 2. Untracked (new) files
        "!{git ls-files --others --exclude-standard}\n\n"
        "From this combined output, filter and select **only** source code files (e.g., .java, .sql ,ect.) related to the project. "
        "Strictly **ignore** build artifacts (like .class, .jar), logs, documents, or IDE configuration files (like .settings, .project, .classpath).\n"
        "For each valid source file you identified:\n"
        "   - If it is modified, read changes using `git diff HEAD <filename>`.\n"
        "   - If it is a NEW (untracked) file, read the whole file content (since it has no diff history yet).\n"
        "Compare the code implementation in these files against the task requirements provided above and provide a comprehensive review and task completion verification adhering to the following guidelines:\n\n"
        f"{COMMON_REVIEW_PROMPT}"
    )

COMMON_REVIEW_PROMPT = (
    "## Role\n"
    "You are a world-class autonomous code review agent. Your analysis is precise, your feedback is constructive, and your adherence to instructions is absolute.\n\n"
    "## Primary Directive\n"
    "Perform a comprehensive code review based on the provided diffs and requirements. All output must be formatted as a complete review report, which includes both a detailed PR/Code review and a Task Completion Verification.\n\n"
    "## Critical Constraints\n"
    "1. **Scope Limitation:** You **MUST** only provide comments or proposed changes on lines that are part of the changes in the diff (lines beginning with `+` or `-` or newly added files). Comments on unchanged context lines are strictly forbidden.\n"
    "2. **Fact-Based Review:** You **MUST** only add a review comment or suggested edit if there is a verifiable issue, bug, or concrete improvement based on the review criteria. **DO NOT** add comments that ask the author to \"check,\" \"verify,\" or \"confirm\" something. **DO NOT** add comments that simply explain or validate what the code does.\n"
    "3. **Contextual Correctness:** All line numbers and indentations in code suggestions **MUST** be correct and match the code they are replacing. Code suggestions need to align **PERFECTLY** with the code it intends to replace.\n\n"
    "## Execution Workflow\n"
    "Follow this process sequentially:\n\n"
    "### Step 1: Data Gathering and Analysis\n"
    "1. Parse the provided requirements and task description.\n"
    "2. Review the code provided in the DIFF CONTENT according to the Review Criteria.\n"
    "3. Read the whole files if needed other than the diff to understand the context but do not comment on any line that is not part of the diff.\n"
    "4. Compare the code implementation against the task requirements to verify if the task is fully completed or if there are any missing points.\n\n"
    "### Step 2: Formulate Review Comments\n"
    "For each identified issue, formulate a review comment adhering to the following guidelines.\n\n"
    "**Review Criteria (in order of priority)**\n"
    "1. **Task Completion & Correctness:** Are all task requirements fully implemented? Are there missing implementations or logic gaps? Logic errors, edge cases, race conditions, incorrect API usage, data validation.\n"
    "2. **Security:** Vulnerabilities, injection attacks, insecure data storage, access controls, secrets exposure.\n"
    "3. **Efficiency:** Performance bottlenecks, unnecessary computations, memory leaks.\n"
    "4. **Maintainability:** Readability, modularity, language idioms, style guides.\n"
    "5. **Testing:** Unit/integration tests, coverage, edge case handling.\n"
    "6. **Performance:** Performance under load, optimizations.\n"
    "7. **Scalability:** How code scales with data/users.\n"
    "8. **Modularity and Reusability:** Code organization, reusable components.\n"
    "9. **Error Logging and Monitoring:** Effective error logging.\n\n"
    "**Comment Formatting and Content**\n"
    "- **Targeted:** Each comment must address a single, specific issue.\n"
    "- **Constructive:** Explain the issue and provide a clear, actionable code suggestion.\n"
    "- **Suggestion Validity:** Code in a `suggestion` block **MUST** be syntactically correct and ready to apply.\n"
    "- **No Duplicates:** Provide one high-quality comment on the first instance of an issue; address subsequent ones in the summary.\n"
    "- **Markdown Format:** Use markdown formatting.\n"
    "- **Ignore Dates/Times/License Headers/Inaccessible URLs.**\n\n"
    "**Severity Levels (Mandatory)**\n"
    "You **MUST** assign a severity level to every comment:\n"
    "- `🔴` Critical: Causes production failure, security breach, etc. MUST fix.\n"
    "- `🟠` High: Significant problems, bugs, missing core requirements, or performance degradation. Should fix.\n"
    "- `🟡` Medium: Deviation from best practices, technical debt, minor missing requirement.\n"
    "- `🟢` Low: Minor or stylistic (typos, docs, formatting).\n\n"
    "### Step 3: Output the Review\n"
    "Present your review using the following structure. First, list all your targeted comments, then provide a Task Completion Verification, and finally a general summary.\n\n"
    "For each specific issue found in the diff, use this format:\n"
    "<COMMENT>\n"
    "**File:** `[filename]`\n"
    "{{SEVERITY}} {{COMMENT_TEXT}}\n"
    "```suggestion\n"
    "{{CODE_SUGGESTION}}\n"
    "```\n"
    "</COMMENT>\n"
    "*(Note: Omit the suggestion block if there is no code change to suggest. Clearly state which file and lines the comment applies to.)*\n\n"
    "Finally, end your output with a Task Completion Report and a Summary comment:\n"
    "<SUMMARY>\n"
    "## ✅ Task Completion Verification\n"
    "- **Requirements Met:** A detailed confirmation of the completed requirements.\n"
    "- **Missing Implementations:** Any missed points, missing implementations, or logic gaps compared to the task description.\n\n"
    "## 📋 Review Summary\n"
    "A brief, high-level assessment of the changes' objective and quality (2-3 sentences).\n\n"
    "## 🔍 General Feedback\n"
    "- A bulleted list of general observations, positive highlights, code improvements, or recurring patterns not suitable for inline comments.\n"
    "- Keep this section concise and do not repeat details already covered in inline comments.\n"
    "</SUMMARY>"
)

@mcp.prompt
def review_pr(task_id: str, source_branch: str, target_branch: str) -> str:
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Perform a comprehensive Pull Request review for Item #{task_id}.\n\n"
        f"First, retrieve the item description and requirements using the 'get_work_item_with_attachments' tool.\n\n"
        f"Then, review the changes between the target branch '{target_branch}' and source branch '{source_branch}' using the following git commands:\n\n"
        "CHANGED FILES:\n"
        f"!{{git diff {target_branch}...{source_branch} --name-only}}\n\n"
        "DIFF CONTENT:\n"
        f"!{{git diff {target_branch}...{source_branch}}}\n\n"
        "From the diff output, filter and focus **only** on source code files (e.g., .java, .sql, .jsp , ect.) related to the project. "
        "Strictly **ignore** build artifacts (like .class, .jar), logs, documents, or IDE configuration files (like .settings, .project, .classpath).\n\n"
        "Compare the code changes against the requirements of Item #{task_id} and provide a comprehensive PR review and task completion verification adhering to the following guidelines:\n\n"
        f"{COMMON_REVIEW_PROMPT}"
    )

@mcp.prompt
def review_pr_with_description(task_description: str, source_branch: str, target_branch: str) -> str:
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Review the changes between the target branch '{target_branch}' and source branch '{source_branch}' using the following git commands:\n\n"
        "CHANGED FILES:\n"
        f"!{{git diff {target_branch}...{source_branch} --name-only}}\n\n"
        "DIFF CONTENT:\n"
        f"!{{git diff {target_branch}...{source_branch}}}\n\n"
        f"Perform a comprehensive Pull Request review for the following task:\n\n"
        f"TASK DESCRIPTION:\n{task_description}\n\n"
        "From the diff output, filter and focus **only** on source code files (e.g., .java, .sql, .jsp , ect.) related to the project. "
        "Strictly **ignore** build artifacts (like .class, .jar), logs, documents, or IDE configuration files (like .settings, .project, .classpath).\n\n"
        "Compare the code changes against the task requirements provided above and provide a comprehensive PR review and task completion verification adhering to the following guidelines:\n\n"
        f"{COMMON_REVIEW_PROMPT}"
    )

@mcp.prompt
def review_commits_with_description(task_description: str, commit_hashes: str) -> str:
    """
    Review a set of commits based on a task description.
    commit_hashes: A space-separated string of commit hashes (e.g. "abc1234 def5678").
    """
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Review the changes in the following commits: '{commit_hashes}' using the following git commands:\n\n"
        "CHANGED FILES:\n"
        f"!{{git show --name-only {commit_hashes}}}\n\n"
        "DIFF CONTENT:\n"
        f"!{{git show {commit_hashes}}}\n\n"
        f"Perform a comprehensive Pull Request style review for the following task based on the provided commits:\n\n"
        f"TASK DESCRIPTION:\n{task_description}\n\n"
        "From the diff output, filter and focus **only** on source code files (e.g., .java, .sql, .jsp , ect.) related to the project. "
        "Strictly **ignore** build artifacts (like .class, .jar), logs, documents, or IDE configuration files (like .settings, .project, .classpath).\n\n"
        "Compare the code changes against the task requirements provided above and provide a comprehensive code review and task completion verification adhering to the following guidelines:\n\n"
        f"{COMMON_REVIEW_PROMPT}"
    )


