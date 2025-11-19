import re
import html
from typing import Dict, Optional
import hashlib
from datetime import datetime

from src.core.config import settings

# Constants
GITHUB_URL_PATTERN = re.compile(r'^https://github\.com/([a-zA-Z0-9-]+)/([a-zA-Z0-9-_.]+)/?$')
MARKDOWN_LIST_PATTERNS = {
    'numbered': re.compile(r'^\d+\.\s'),
    'bullet': re.compile(r'^[-*]\s')
}

def validate_github_url(url: str) -> bool:
    """
    Validate a GitHub repository URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    return bool(GITHUB_URL_PATTERN.match(url))

def extract_repo_info(github_url: str) -> Dict[str, str]:
    """
    Extract repository information from a GitHub URL.
    
    Args:
        github_url: Full GitHub repository URL
        
    Returns:
        Dict containing owner, repo name, and full_name
        
    Raises:
        ValueError: If URL format is invalid
    """
    match = GITHUB_URL_PATTERN.match(github_url)
    if not match:
        raise ValueError("Invalid GitHub URL format")
        
    owner, repo = match.groups()
    return {
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}"
    }

def generate_content_hash(content: str, algorithm: str = 'sha256') -> str:
    """
    Generate cryptographic hash of content.
    
    Args:
        content: Content to hash
        algorithm: Hash algorithm to use ('sha256' or 'sha512')
        
    Returns:
        str: Hex digest of hash
    """
    if algorithm not in ('sha256', 'sha512'):
        raise ValueError("Unsupported hash algorithm")
        
    hasher = hashlib.new(algorithm)
    hasher.update(content.encode())
    return hasher.hexdigest()

def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing harmful content.
    
    Args:
        text: Input text to sanitize
        max_length: Optional maximum length
        
    Returns:
        str: Sanitized text
    """
    # Basic XSS protection
    text = html.escape(text.strip())
    
    # Bleach removed to reduce dependencies
    # text = bleach.clean(text)
    
    # Enforce length limit if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
        
    return text

def format_ai_response(response: str) -> str:
    """
    Format AI response with consistent Markdown styling.
    
    Args:
        response: Raw AI response text
        
    Returns:
        str: Formatted Markdown text
    """
    if not response:
        return ""
        
    lines = response.strip().split('\n')
    formatted = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted.append("")
            continue
            
        # Format numbered lists
        if MARKDOWN_LIST_PATTERNS['numbered'].match(line):
            formatted.append(f"**{line}**")
        # Format bullet points
        elif MARKDOWN_LIST_PATTERNS['bullet'].match(line):
            formatted.append(f"• {line[1:].strip()}")
        # Format code blocks
        elif line.startswith('```'):
            formatted.append(line)
        # Normal text
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)