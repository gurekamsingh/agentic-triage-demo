#!/usr/bin/env python3
"""
agent/triage.py — Agentic bug triage using Claude tool-use loop.
"""

import json
import os
import anthropic
from github import Github

gh     = Github(os.environ["GITHUB_TOKEN"])
repo   = gh.get_repo(os.environ["REPO_NAME"])
client = anthropic.Anthropic()

ISSUE_NUMBER = int(os.environ["ISSUE_NUMBER"])
ISSUE_TITLE  = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY   = os.environ.get("ISSUE_BODY", "")

TOOLS = [
    {
        "name": "add_label",
        "description": "Add a label to the issue. Valid labels: bug, enhancement, question, needs-info, security, duplicate, wontfix.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"}
            },
            "required": ["label"],
        },
    },
    {
        "name": "post_comment",
        "description": "Post a comment on the issue visible to the reporter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "body": {"type": "string"}
            },
            "required": ["body"],
        },
    },
    {
        "name": "search_similar_issues",
        "description": "Search for existing open or closed issues similar to the current one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_file_contents",
        "description": "Read a file from the repository to understand context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"],
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    issue = repo.get_issue(ISSUE_NUMBER)

    if name == "add_label":
        label = args["label"]
        try:
            issue.add_to_labels(label)
            return f"Label '{label}' added."
        except Exception as e:
            return f"Failed to add label: {e}"

    elif name == "post_comment":
        issue.create_comment(args["body"])
        return "Comment posted."

    elif name == "search_similar_issues":
        results = gh.search_issues(
            query=f"{args['query']} repo:{os.environ['REPO_NAME']}"
        )
        found = []
        for i, item in enumerate(results):
            if i >= 5:
                break
            found.append(f"#{item.number}: {item.title} [{item.state}]")
        return "\n".join(found) if found else "No similar issues found."

    elif name == "get_file_contents":
        try:
            contents = repo.get_contents(args["path"])
            return contents.decoded_content.decode("utf-8")[:3000]
        except Exception as e:
            return f"Could not read file: {e}"

    return f"Unknown tool: {name}"


def run_agent():
    system_prompt = """You are a senior engineer triaging GitHub issues for a FastAPI task manager app.

Steps:
1. Search for duplicates first.
2. Read the relevant source file if needed to understand the bug.
3. Add the appropriate label: bug, enhancement, question, needs-info, security, duplicate, or wontfix.
4. Post a concise, helpful comment:
   - For bugs: acknowledge it, ask for repro steps / Python version / OS if not provided.
   - For features: acknowledge and note it will be reviewed.
   - For security issues: label as 'security', post a generic acknowledgement only — no public repro steps.
   - For duplicates: link to the original issue.
5. Stop once you have labelled and commented."""

    messages = [
        {
            "role": "user",
            "content": f"New issue #{ISSUE_NUMBER}\n\nTitle: {ISSUE_TITLE}\n\nBody:\n{ISSUE_BODY}",
        }
    ]

    print(f"[agent] Triaging issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")

    for i in range(10):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        print(f"[agent] Step {i+1} — stop_reason: {response.stop_reason}")
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print("[agent] Done.")
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"[agent] → {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                print(f"[agent] ← {result[:150]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_agent()