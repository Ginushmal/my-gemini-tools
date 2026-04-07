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

