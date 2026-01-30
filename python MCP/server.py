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
def greet(name:str) -> str:
    """Returns a friendly greeting"""
    return f"Hello {name}! Its a pleasure to connect from your first MCP Server."


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

@mcp.prompt
def generate_commit_message() -> str:
    return (
    "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
    f"Please generate a Conventional Commit message and a description for it based on the following git diff. The commit message should include 'feature :' as a prefix if the task I'm working on is a feature, or 'fix :' prefix if it is a bug fix. Ignore the .md files in the diff and any files that are in the .gemini folder; only consider the changes done to *.java , *.sql , *.prc files and *.jsp files (Ignore the BACKOFFICE.sql file tho). "
    "The description should be concise and point-wise without a hierarchical structure, highlight the main changes made after the last commit, and include all and every change made in the diff. Do not leave anything out. Include what you did and how you did it too in the description.\n\n"
    "DIFF FILES:\n"
    "!{git diff HEAD --name-only}\n\n"
    "DIFF CONTENT:\n"
    "!{git diff HEAD [list of file names]}\n"
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
        f"Compare the code implementation in these files against the requirements of Item #{task_id} to verify if the task is fully completed.\n"
        "Finally, provide a full report detailing:\n"
        "1. Confirmation of completed requirements.\n"
        "2. Any missing implementations or logic gaps.\n"
        "3. Specific suggestions for code improvements."
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
        "Compare the code implementation in these files against the task requirements provided above to verify if the task is fully completed.\n"
        "Finally, provide a full report detailing:\n"
        "1. Confirmation of completed requirements.\n"
        "2. Any missing implementations or logic gaps.\n"
        "3. Specific suggestions for code improvements."
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
        f"Compare the code changes against the requirements of Item #{task_id} and provide a comprehensive PR review covering:\n"
        "1. **Requirements Verification**: Confirm that all requirements are implemented correctly.\n"
        "2. **Code Quality**: Assess code structure, readability, and adherence to best practices.\n"
        "3. **Potential Issues**: Identify any bugs, logic errors, or edge cases not handled.\n"
        "4. **Security Concerns**: Point out any security vulnerabilities or risks.\n"
        "5. **Performance**: Highlight any performance issues or inefficiencies.\n"
        "6. **Testing**: Verify if adequate test coverage exists for the changes.\n"
        "7. **Suggestions**: Provide specific, actionable suggestions for improvements.\n\n"
        "Format your review with clear sections and prioritize critical issues first."
    )

@mcp.prompt
def review_pr_with_description(task_description: str, source_branch: str, target_branch: str) -> str:
    return (
        "**IMPORTANT**: Ensure you navigate to the correct project root folder before running any git commands. The CLI might be opened from an outer parent folder.\n\n"
        f"Perform a comprehensive Pull Request review for the following task:\n\n"
        f"TASK DESCRIPTION:\n{task_description}\n\n"
        f"Review the changes between the target branch '{target_branch}' and source branch '{source_branch}' using the following git commands:\n\n"
        "CHANGED FILES:\n"
        f"!{{git diff {target_branch}...{source_branch} --name-only}}\n\n"
        "DIFF CONTENT:\n"
        f"!{{git diff {target_branch}...{source_branch}}}\n\n"
        "From the diff output, filter and focus **only** on source code files (e.g., .java, .sql, .jsp , ect.) related to the project. "
        "Strictly **ignore** build artifacts (like .class, .jar), logs, documents, or IDE configuration files (like .settings, .project, .classpath).\n\n"
        "Compare the code changes against the task requirements provided above and provide a comprehensive PR review covering:\n"
        "1. **Requirements Verification**: Confirm that all requirements are implemented correctly.\n"
        "2. **Code Quality**: Assess code structure, readability, and adherence to best practices.\n"
        "3. **Potential Issues**: Identify any bugs, logic errors, or edge cases not handled.\n"
        "4. **Security Concerns**: Point out any security vulnerabilities or risks.\n"
        "5. **Performance**: Highlight any performance issues or inefficiencies.\n"
        "6. **Testing**: Verify if adequate test coverage exists for the changes.\n"
        "7. **Suggestions**: Provide specific, actionable suggestions for improvements.\n\n"
        "Format your review with clear sections and prioritize critical issues first."
    )


