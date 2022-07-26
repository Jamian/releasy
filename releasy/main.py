
from cmath import e
import os
import pathlib
import re
import webbrowser

import click
import requests

from urllib.parse import urljoin


class JiraClient():
    _email = None
    _api_key = None
    _url_base = os.environ['RELEASY_JIRA_BASE_URL']

    def __init__(self, email: str, api_key: str) -> None:
        self._email = email
        self._api_key = api_key
        self._auth = requests.auth.HTTPBasicAuth(email, api_key)

    def get_issues(self, project: str, version: str) -> list:
        """Fetches and returns a list of issues related to a release from Jira.

        Args:
            project (str): the Jira project key.
            version (str): the Jira release version for which to fetch issues.

        Returns:
            list: list of issues from Jira.
        """
        # TODO : Handle pagination
        endpoint = urljoin(self._url_base, '/rest/api/3/search')

        response = requests.get(endpoint, params={'jql': f'project={project}&fixVersion={version}'}, auth=self._auth).json()
        issues = []
        if not 'errorMessages' in response:
            total_results = response['total']
            issues = response['issues']

            while len(issues) != total_results:
                response = requests.get(endpoint, params={'startAt': len(issues), 'jql': f'project={project}&fixVersion={version}'}, auth=self._auth).json()
                issues = issues + response['issues']

        return issues

    def get_dev_status(self, issue_id: str) -> list:
        endpoint = urljoin(self._url_base, f'/rest/dev-status/latest/issue/detail?issueId={issue_id}&applicationType=GitHub&dataType=repository')
        headers = {
            'Accept': 'application/json'
        }
        response = requests.get(endpoint, headers=headers, auth=self._auth)
        return response.json()

    def get_releases(self, project_key: str) -> list:
        endpoint = urljoin(self._url_base, f'/rest/api/3/project/{project_key}/version')
        # TODO : Handle Pagination
        response = requests.get(endpoint, auth=self._auth)
        return response.json()['values']

def _is_iac(repo_name: str, pattern: str) -> bool:
    """Using the provided regex, checks whether this repo is an IAC repo or not.

    Args:
        repo_name (str): The name of the repo to check whether it is an IAC repo or not.
        pattern (str): The Regex pattern to match the repo name against.

    Returns:
        bool: True if the repo is of type IAC.
    """
    compiled_pattern = re.compile(pattern)
    return compiled_pattern.match(repo_name)


@click.command()
@click.option('--version', help='The Release Version from Jira to Generate notes for.')
@click.option('--projects', help='Comma separated list of Jira Projects to check.')
@click.option('--jira-auth-username', default=None, help='The username to authenticate with Jira.')
@click.option('--jira-auth-api-key', default=None, help='The Jira API Key to authenticate with Jira.')
@click.option('--iac-re-pattern', default='^terraform-layer-.*$', help='The regex pattern to match IAC repositories against.')
@click.option('--git-base-url', help='The base url to the git-based source code repository.')
def run(version, projects, jira_auth_username, jira_auth_api_key, iac_re_pattern, git_base_url):

    if not version:
        raise ValueError('Missing required input "version". Please see help.')
    if not projects:
        raise ValueError('Missing required input "projects". Please see help.')

    if not jira_auth_username:
        try:
            jira_auth_username = os.environ['RELEASY_JIRA_AUTH_USERNAME']
        except KeyError:
            print('Please set "--jira-auth-username" or the environment variable "RELEASY_JIRA_AUTH_USERNAME".')
            exit(1)
    if not jira_auth_api_key:
        try:
            jira_auth_api_key = os.environ['RELEASY_JIRA_AUTH_API_KEY']
        except KeyError:
            print('Please set "--jira-auth-api-key" or the environment variable "RELEASY_JIRA_AUTH_API_KEY".')
            exit(1)

    if not git_base_url:
        try:
            git_base_url = os.environ['RELEASY_GIT_BASE_URL']
        except KeyError:
            pass
        
    jira_client = JiraClient(jira_auth_username, jira_auth_api_key)

    issues = []
    for project in projects.split(','):
        issues = issues + jira_client.get_issues(project=project, version=version)

    changed_app_projects = set()
    changed_iac_projects = set()
    changed_project_repos = {}

    for issue in issues:
        response = jira_client.get_dev_status(issue['id'])
        for detail in response['detail']:
            for repo in detail['repositories']:
                repo_name = repo['name']
                if _is_iac(repo_name, iac_re_pattern):
                    for commit in repo['commits']:
                        for file in commit['files']:
                            project_path_parts = file['path'].split('/')
                            path = '/'.join(project_path_parts[:-1])
                            changed_iac_projects.add(f'{repo_name}/{path}')
                            changed_project_repos[f'{repo_name}/{path}'] = repo['url']
                else:
                    if repo_name not in changed_app_projects:
                        changed_app_projects.add(repo_name)
                        changed_project_repos[repo_name] = repo['url']

    m_dir = pathlib.Path(__file__).parent.resolve()
    index_html = open(os.path.join(m_dir, 'templates/index.html.template'), 'r').read()
    index_html = index_html.replace('[[ release_version ]]', version)
    app_table_body_html = ""
    for project in changed_app_projects:
        anchor_html = f'<a target="_blank" href={git_base_url}/>' if git_base_url is not None else f'<a target="_blank" href={changed_project_repos[project]}/>'
        app_table_body_html = app_table_body_html + f"""        <tr>
                <td>{anchor_html}{project}</td>
            </tr>
    """

    iac_table_body_html = ""
    for project in changed_iac_projects:
        anchor_html = f'<a target="_blank" href={git_base_url}/>' if git_base_url is not None else f'<a target="_blank" href={changed_project_repos[project]}/>'
        iac_table_body_html = iac_table_body_html + f"""        <tr>
                <td>{anchor_html}{project}</td>
            </tr>
    """

    index_html = index_html.replace('[[ app_table_body ]]', app_table_body_html)
    index_html = index_html.replace('[[ iac_table_body ]]', iac_table_body_html)

    index_path = os.path.join(os.getcwd(), 'index.html')
    with open(index_path, 'w') as f:
        f.write(index_html)

    webbrowser.open(f'file://{index_path}', new=2)
