Gemini CLI 🤝 FastMCP
As of FastMCP v2.12.3, you can now install local STDIO transport MCP servers built with FastMCP using the fastmcp install gemini-cli command.

```
fastmcp install gemini-cli server.py
```

This command simplifies the process and makes your FastMCP server's capabilities instantly available and configured within Gemini CLI! It automatically handles the configuration, dependency management, and calls Gemini CLI’s built-in MCP management system (gemini mcp add). For local server development, this integration offers a convenient way to get started.

activate the v env :

```
.venv\Scripts\activate
```

install packages with :

```
uv pip install <package_name>
```

run fast mcp server with

```
fastmcp dev server.py --ui-port="9080" --server-port="5080"
```

to test for errors , full cmd command :

```
uv run --with fastmcp --with pandas --with openpyxl fastmcp run "D:\my-gemini-tools\python MCP\server.py"
```

add this as the MCP server

```
    "MyFirstMCPServer": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "--with",
        "pandas",
        "--with",
        "openpyxl",
        "--with",
        "xlrd",
        "fastmcp",
        "run",
        "D:\\my-gemini-tools\\python MCP\\server.py"
      ]
    },

```

guid :
[Building your own MCP Server](https://medium.com/google-cloud/gemini-cli-tutorial-series-part-8-building-your-own-mcp-server-74d6add81cca)
