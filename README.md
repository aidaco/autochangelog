# GitHub Actions Autochangelog

This GitHub Action automatically generates a user-friendly changelog from pull requests. It is designed to be used in a CI/CD pipeline to provide a clear and concise summary of changes for non-technical audiences.

## How it Works

The core of the project is a Python script that uses the AWS Bedrock service to interact with the Anthropic Claude Sonnet 4.5 large language model. The script gathers the git history of a pull request, sends it to the model with a detailed prompt, and formats the model's response as a changelog.

The action is configured to run on every pull request to the `main` branch. It will post the generated changelog as a comment on the pull request, and update it if the pull request is updated.

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
3.  Run the `generate_changelog.py` script with the base and head refs:

```bash
uv run python generate_changelog.py <base_ref> <head_ref>
```

This will print the changelog to standard output.