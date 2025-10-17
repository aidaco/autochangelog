# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "boto3",
#     "python-dotenv"
# ]
# ///

import time
import subprocess
import sys
import argparse
import logging
import json
import boto3
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def invoke_anthropic(client, model_id: str, prompt: str, max_tokens: int = 4000) -> str:
    try:
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ]
        body = {
            "messages": messages,
            "max_tokens": max_tokens,
            "anthropic_version": "bedrock-2023-05-31",
        }
        start = time.perf_counter()
        response = client.invoke_model(
            modelId=model_id, body=json.dumps(body), contentType="application/json"
        )
        body = response["body"].read()
        logger.info(f"Finished generation in {time.perf_counter() - start:.2f}s")
        content = json.loads(body)["content"]
        return "\n".join(block["text"] for block in content)
    except Exception as exc:
        logger.error(f"An error occurred while invoking the LLM {exc}")
        sys.exit(1)


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


def generate_changelog(base_ref: str, head_ref: str, prompt_template: str) -> str:
    context = {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "git_log": run_shell(["git", "log", f"{base_ref}..{head_ref}"]),
        "git_diff": run_shell(["git", "diff", f"{base_ref}..{head_ref}"]),
    }
    prompt = prompt_template.format(**context)
    logger.info(f"Prompt is: {prompt}")
    client = boto3.client("bedrock-runtime")
    try:
        text = invoke_anthropic(client, MODEL_ID, prompt)
        logger.info(f"Generated changelog: {text}")
        return text
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    parser = argparse.ArgumentParser(prog="generate_changelog")
    parser.add_argument("base_ref")
    parser.add_argument("head_ref")
    parser.add_argument("-p", "--prompt-file")
    args = parser.parse_args()
    if not args.base_ref or not args.head_ref:
        logger.error("Must provide both base_ref and head_ref.")
        sys.exit(1)

    if args.prompt_file:
        prompt_path = Path(args.prompt_file)
    else:
        prompt_path = Path(__file__).parent/'prompts'/'internal.md'
    try:
        prompt_template = prompt_path.read_text()
    except FileNotFoundError:
        logger.error(f"Prompt file not found at {args.prompt_file}")
        sys.exit(1)

    text = generate_changelog(args.base_ref, args.head_ref, prompt_template)
    print(text)
