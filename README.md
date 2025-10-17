# GitHub Actions Autochangelog

This GitHub Action automatically generates a user-friendly changelog from pull requests. It is designed to be used in a CI/CD pipeline to provide a clear and concise summary of changes for both technical and non-technical audiences.

## How it Works

The core of the project is a Python script that uses the AWS Bedrock service to interact with the Anthropic Claude Sonnet 4.5 large language model. The script gathers the git history of a pull request, sends it to the model with a detailed prompt, and formats the model's response as a changelog.

The action is a composite action that runs the Python script. It can be configured to use different prompts to generate different types of changelogs. The included workflow runs the action twice to generate two distinct changelogs:

*   **External Changelog:** A user-friendly summary of changes for non-technical audiences.
*   **Internal Changelog:** A comprehensive summary of all changes for internal stakeholders (developers, QA, etc.).

The workflow is configured to run on every pull request to the `main` branch. It will post both changelogs as a comment on the pull request, each within a collapsible "details" element. The comment will be updated if the pull request is updated.

## Usage

To use this action in your own repository, create a workflow file (e.g., `.github/workflows/generate-changelog.yml`) with the following content:

```yaml
name: Generate Changelog
on:
  pull_request:
    types:
      - opened
      - synchronize
    branches:
      - main
jobs:
  generate-changelog:
    name: Generate Changelog
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - name: Generate internal changelog
        id: generate-internal-changelog
        uses: ./
        with:
          prompt-preset: internal
          base-ref: ${{github.base_ref}}
          head-ref: ${{github.head_ref}}
        env:
          AWS_ACCESS_KEY_ID: ${{secrets.AWS_ACCESS_KEY_ID}}
          AWS_SECRET_ACCESS_KEY: ${{secrets.AWS_SECRET_ACCESS_KEY}}
          AWS_DEFAULT_REGION: ${{vars.AWS_DEFAULT_REGION}}
      - name: Generate external changelog
        id: generate-external-changelog
        uses: ./
        with:
          prompt-preset: external
          base-ref: ${{github.base_ref}}
          head-ref: ${{github.head_ref}}
        env:
          AWS_ACCESS_KEY_ID: ${{secrets.AWS_ACCESS_KEY_ID}}
          AWS_SECRET_ACCESS_KEY: ${{secrets.AWS_SECRET_ACCESS_KEY}}
          AWS_DEFAULT_REGION: ${{vars.AWS_DEFAULT_REGION}}
      - name: Comment on PR
        uses: actions/github-script@v7
        env:
          INTERNAL_CHANGELOG: ${{steps.generate-internal-changelog.outputs.changelog}}
          EXTERNAL_CHANGELOG: ${{steps.generate-external-changelog.outputs.changelog}}
        with:
          github-token: ${{secrets.GITHUB_TOKEN}}
          script: |
            const header = '### Automated Changelog';
            const internal = `<details><summary>Internal</summary>\n\n${process.env.INTERNAL_CHANGELOG}</details>`
            const external = `<details><summary>External</summary>\n\n${process.env.EXTERNAL_CHANGELOG}</details>`
            const body = header + "\n\n" + internal + "\n\n" + external;

            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            const existingComment = comments.find(comment => 
              comment.user.login === 'github-actions[bot]' && comment.body.startsWith(header)
            );

            if (existingComment) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existingComment.id,
                body: body
              });
            } else {
              await github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: body
              });
            }
```

You will also need to create the following secrets and variables in your repository's settings:
*   `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
*   `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
*   `AWS_DEFAULT_REGION`: The AWS region where you want to run the Bedrock service.

## Action Inputs

| Name | Description | Default | 
|---|---|---|
| `prompt-preset` | The name of the prompt preset to use from the `prompts` directory (without the `.md` extension). | `internal` |
| `prompt-file` | The path to a custom prompt file to use. | |
| `base-ref` | The base git ref to compare against. | **Required** |
| `head-ref` | The head git ref to compare against. | **Required** |

## Action Outputs

| Name | Description |
|---|---|
| `changelog` | The generated changelog text. |

## Local Development & Manual Changelog Generation

You can run the script locally to generate a changelog for any two git refs.

1.  Install Python 3.12+ and `uv`.
2.  Create a `.env` file with the necessary AWS credentials. You can use `.env.sample` as a template.
3.  Run the `generate_changelog.py` script with the base and head refs, specifying which prompt to use:

```bash
# Generate the external changelog
uv run python generate_changelog.py -p prompts/external.md <base_ref> <head_ref>

# Generate the internal changelog
uv run python generate_changelog.py -p prompts/internal.md <base_ref> <head_ref>
```

This will print the changelog to standard output.

## Prompts

The prompts used to generate the changelogs are located in the `prompts` directory:

*   `external.md`: This prompt is designed to generate a changelog for a non-technical audience. It focuses on the user-facing changes and the value they provide.
*   `internal.md`: This prompt is designed to generate a changelog for an internal audience. It includes all significant changes, including internal refactoring, dependency updates, and CI/CD changes.

You can customize these prompts to fit your needs.