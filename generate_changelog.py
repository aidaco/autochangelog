# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "boto3",
#     "python-dotenv"
# ]
# ///

import time
import subprocess
from typing import Literal, TypedDict
import sys
import argparse
import logging
import json
import boto3
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
PROMPT = """\
You are an expert technical writer and product manager. Your task is to create a clear, concise, and user-friendly changelog from a series of git commits and pull request data.
Your audience is non-technical--the end-user of the application. Your goal is to translate technical development history into an easy-to-understand summary of what has changed, focusing on the value and impact to the user.

INSTRUCTIONS
Analyze the Data: Review the Git Log and the Diff provided above to understand the changes made.
Identify User-Facing Changes: Focus exclusively on changes that directly affect the user experience or add value.
Ignore Internal Changes: You MUST ignore commits and PRs related to:
 - Internal chores
 - Code refactoring
 - Documentation updates
 - Dependency bumps or version updates
 - CI/CD configuration
 - Tests
 - Code style changes
...unless they result in a direct and noticeable benefit to the end-user (e.g., a major performance improvement).
Categorize the Changes: Group each user-facing change into one of the following categories. If a category has no items for this release, omit it entirely from the final output.
 - Features: For brand-new functionality and major additions.
 - Improvements: For enhancements to existing features, performance upgrades, or UI/UX updates.
 - Fixes: For resolving errors, crashes, or incorrect behavior.
Rewrite for Clarity: DO NOT use raw commit messages or PR titles. Rephrase each item from an end-user's perspective.
Focus on the benefit: Explain what the user can do now or why the change is helpful.
Use simple language: Avoid technical jargon, internal project names, and implementation details.Bad
Format the Output: Provide the final output in clean Markdown. List each changelog item as a bullet point (-).

EXAMPLE OUTPUT
```
### Features
- You can now export your monthly reports as a PDF file for easy sharing.
- We've added a dark mode! You can enable it from your account settings page.

### Improvements
- The main dashboard now loads significantly faster, especially for accounts with many projects.
- The design of the buttons across the app has been updated for better visibility and a more modern look.

### Fixes
- Fixed an issue that caused the application to crash when uploading a file with a very long name.
- Corrected a calculation error in the annual summary dashboard.
````

CONTEXT
PR from base ref '{base_ref}' to head ref '{head_ref}'

The following output of `git log {base_ref}..{head_ref}` contains the titles and descriptions of all changes between the two refs. This is your primary source of information.
```
{git_log}
```

You may also find the output of `git diff` helpful. Use it for additional context, but do not reference code directly in your output.
```
{git_diff}
```
"""


class TextContent(TypedDict):
    text: str
    type: str


type Content = TextContent  # | ImageContent, etc.


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: list[Content]


def invoke_anthropic(
    client, model_id: str, messages: list[Message], max_tokens: int = 4000
) -> Message:
    try:
        body = {
            "messages": messages,
            "max_tokens": max_tokens,
            "anthropic_version": "bedrock-2023-05-31",
        }
        response = client.invoke_model(
            modelId=model_id, body=json.dumps(body), contentType="application/json"
        )
        body = response["body"].read()
        return {"role": "assistant", "content": json.loads(body)["content"]}
    except Exception as exc:
        logger.error(f"An error occurred while invoking the LLM {exc}")
        sys.exit(1)


def generate_response(client, model_id: str, prompt: str) -> str:
    response = invoke_anthropic(
        client,
        model_id,
        [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    )
    return "\n".join(block["text"] for block in response["content"])


def run_shell(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running '{' '.join(cmd)}'.")
        print(f"Return Code: {e.returncode}")
        print(f"Error Output:\n---\n{e.stderr.strip()}\n---")
        sys.exit(1)


def main(base_ref: str, head_ref: str):
    if not base_ref or not head_ref:
        logger.error("Must provide both base_ref and head_ref.")
        sys.exit(1)
    context = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "git_log": run_shell(["git", "log", f"{base_ref}..{head_ref}"]),
        "git_dif": run_shell(["git", "diff", f"{base_ref}..{head_ref}"]),
    }
    prompt = PROMPT.format(**context)
    client = boto3.client("bedrock-runtime")
    start = time.perf_counter()
    text = generate_response(client, MODEL_ID, prompt)
    print(text)
    logger.info(f"Finished generation in {time.perf_counter() - start:.2f}s")
    client.close()


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(prog="generate_changelog")
    parser.add_argument("base_ref")
    parser.add_argument("head_ref")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.base_ref, args.head_ref)
