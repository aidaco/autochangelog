# GitHub Actions Autochangelog

This GitHub Action automatically generates a user-friendly changelog from pull requests. It is designed to be used in a CI/CD pipeline to provide a clear and concise summary of changes for both technical and non-technical audiences.

## How it Works

The core of the project is a Python script that uses the AWS Bedrock service to interact with the Anthropic Claude Sonnet 4.5 large language model. The script gathers the git history of a pull request, sends it to the model with a detailed prompt, and formats the model's response as a changelog.

The action uses two separate prompts to generate two distinct changelogs:

*   **External Changelog:** A user-friendly summary of changes for non-technical audiences.
*   **Internal Changelog:** A comprehensive summary of all changes for internal stakeholders (developers, QA, etc.).

The action is configured to run on every pull request to the `main` branch. It will post both changelogs as a comment on the pull request, each within a collapsible "details" element. The comment will be updated if the pull request is updated.

## Getting Started

To use this action in your own repository:

1.  Copy the `.github/workflows/generate-changelog.yml` file to your repository.
2.  Create the following secrets and variables in your repository's settings:
    *   `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
    *   `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
    *   `AWS_DEFAULT_REGION`: The AWS region where you want to run the Bedrock service.
    *   `GITHUB_TOKEN`: A GitHub token with `pull-requests: write` permissions.

## Local Development & Manual Changelog Generation

You can run the script locally to generate a changelog for any two git refs.

1.  Install Python 3.12+ and `uv`.
2.  Create a `.env` file with the necessary AWS credentials. You can use `.env.sample` as a template.
3.  Run the `generate_changelog.py` script with the base and head refs, specifying which prompt to use:

```bash
# Generate the external changelog
uv run python generate_changelog.py -p external-changelog-prompt.md <base_ref> <head_ref>

# Generate the internal changelog
uv run python generate_changelog.py -p internal-changelog-prompt.md <base_ref> <head_ref>
```

This will print the changelog to standard output.

## Prompts

The prompts used to generate the changelogs are located in the root of the repository:

*   `external-changelog-prompt.md`: This prompt is designed to generate a changelog for a non-technical audience. It focuses on the user-facing changes and the value they provide.
*   `internal-changelog-prompt.md`: This prompt is designed to generate a changelog for an internal audience. It includes all significant changes, including internal refactoring, dependency updates, and CI/CD changes.

You can customize these prompts to fit your needs.
