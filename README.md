# Releasy
![Bandit](https://github.com/jamian/releasy/actions/workflows/bandit.yml/badge.svg)

Sometimes, with complex releases, figuring out where all the different changes have occurred can be overwhelming. Releasy leverages the Jira `dev-status` (and other) APIs to map repositories and code paths back to a Jira Release. This is especially useful if you're trying to figure out all the different Terraform Projects which need to be applied as part of releases.

This handy CLI tool will figure this all out and generate a handy HTML page with a couple of tables to help point you in the right direction.

:warning: The Jira `dev-status` API is not an official / public API and as such is a little lacking in documentation and is subject to undocumented change. For this reason this tool is a fantastic advisor... but take it as the source of all truth at your own peril!

## Contributing
### Local Development Setup

1. `virtualenv -p python3 venv`
2. `pip install -e .`
3. `RELEASY_GIT_BASE_URL=<git-base-url> RELEASY_JIRA_BASE_URL=<jira-base-url> RELEASY_JIRA_AUTH_USERNAME=<jira-email> RELEASY_JIRA_AUTH_API_KEY=<jira-api-key> releasy --version <version> --projects <project1,project2...>`