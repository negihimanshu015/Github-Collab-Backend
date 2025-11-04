from github import Github, GithubException
from src.core.config import settings
from typing import List, Dict, Optional

class GitHubService:
    def __init__(self):
        self.github = Github(settings.GITHUB_ACCESS_TOKEN)
    
    def get_user_repos(self, username: str) -> List[Dict]:
        try:
            user = self.github.get_user(username)
            repos = []
            for repo in user.get_repos():
                repos.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count
                })
            return repos
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    def get_repo_content(self, repo_full_name: str, path: str = "") -> List[Dict]:
        try:
            repo = self.github.get_repo(repo_full_name)
            contents = []
            
            if path:
                items = repo.get_contents(path)
            else:
                items = repo.get_contents("")

            # PyGithub may return a single ContentFile for a file path or a list for a directory.
            # Normalize to a list so callers can iterate safely.
            if not isinstance(items, list):
                items = [items]
            
            for item in items:
                contents.append({
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "url": item.html_url
                })
            
            return contents
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    def get_file_content(self, repo_full_name: str, file_path: str) -> str:
        try:
            repo = self.github.get_repo(repo_full_name)
            file_content = repo.get_contents(file_path)
            # If PyGithub returns a list (unexpected for a file path), pick the first element.
            if isinstance(file_content, list):
                file_content = file_content[0]

            return file_content.decoded_content.decode('utf-8')
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    def create_issue(self, repo_full_name: str, title: str, body: str) -> Dict:
        try:
            repo = self.github.get_repo(repo_full_name)
            issue = repo.create_issue(title=title, body=body)
            return {
                "id": issue.id,
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url
            }
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")