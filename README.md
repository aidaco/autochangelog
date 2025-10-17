# GitHub Actions Autochangelog

This GitHub Action automatically generates a user-friendly changelog from pull requests. It is designed to be used in a CI/CD pipeline to provide a clear and concise summary of changes for both technical and non-technical audiences.

## How it Works

The core of this project is a Python script that leverages the AWS Bedrock service to interact with the Anthropic Claude Sonnet 4.5 large language model. The script analyzes the git history of a pull request, sends it to the model with a detailed prompt, and formats the model's response into a changelog. This process can be customized to generate different types of changelogs by using different prompts.

## Usage

There are three ways to use this autochangelog generator:

### 1. Reusable Workflow

This is the easiest way to use the autochangelog generator. You can call the reusable workflow from your own workflow file. This will generate both an internal and an external changelog and post them as a comment on the pull request.

Create a workflow file (e.g., `.github/workflows/generate-changelog.yml`) with the following content. Make sure to replace `<your-org>/autochangelog` with the correct path to your repository.

```yaml
name: Generate Changelogs
on:
  pull_request:
    types:
      - opened
      - synchronize
    branches:
      - main
jobs:
  generate-changelog:
    permissions:
      contents: read
      pull-requests: write
    uses: aidaco/autochangelog/.github/workflows/generate-changelogs.yml@main
    with:
      aws-default-region: ${{vars.AWS_DEFAULT_REGION}}
  secrets:
    aws-access-key-id: ${{secrets.AWS_ACCESS_KEY_ID}}
    aws-secret-access-key: ${{secrets.AWS_SECRET_ACCESS_KEY}}
    github-token: ${{secrets.GITHUB_TOKEN}}
```

You will also need to create the following secrets and variables in your repository's settings:
*   `AWS_ACCESS_KEY_ID`: Your AWS access key ID.
*   `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.
*   `AWS_DEFAULT_REGION`: (as a variable) The AWS region where you want to run the Bedrock service.

### 2. GitHub Action

You can also use the action directly in your workflow. This gives you more control over how the changelogs are generated and used. For example, you can choose to only generate one type of changelog, or you can use the output of the action in other steps in your workflow.

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
      - name: Generate changelog
        id: generate-changelog
        uses: aidaco/autochangelog@main
        with:
          base-ref: ${{github.base_ref}}
          head-ref: ${{github.head_ref}}
        env:
          AWS_ACCESS_KEY_ID: ${{secrets.AWS_ACCESS_KEY_ID}}
          AWS_SECRET_ACCESS_KEY: ${{secrets.AWS_SECRET_ACCESS_KEY}}
          AWS_DEFAULT_REGION: ${{vars.AWS_DEFAULT_REGION}}
      - name: Write CHANGELOG.md
        env:
          CHANGELOG: ${{steps.generate-changelog.outputs.changelog}}
        run: echo $CHANGELOG > CHANGELOG.md
      - name: Upload CHANGELOG.md
        uses: actions/upload-artifact@v4
        with:
          name: generated-changelog
          path: CHANGELOG.md
```

### 3. Manual Script Execution

You can run the script locally to generate a changelog for any two git refs.

1.  Install `uv`.
2.  Create a `.env` file with the necessary AWS credentials. You can use `.env.sample` as a template.
3.  Run the `generate_changelog.py` script with the base and head refs, specifying which prompt to use:

```bash
uv run python generate_changelog.py <base_ref> <head_ref>
```

This will print the changelog to standard output.

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

## Prompts

The prompts used to generate the changelogs are located in the `prompts` directory:

*   `external.md`: This prompt is designed to generate a changelog for a non-technical audience. It focuses on the user-facing changes and the value they provide.
*   `internal.md`: This prompt is designed to generate a changelog for an internal audience. It includes all significant changes, including internal refactoring, dependency updates, and CI/CD changes.

You can customize these prompts to fit your needs.
