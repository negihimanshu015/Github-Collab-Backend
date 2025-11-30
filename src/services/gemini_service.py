import google.generativeai as genai
from src.core.config import settings
from typing import Optional

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_code_review(self, code: str, context: Optional[str] = None) -> str:
        prompt = f"""
        Please review the following code and provide constructive feedback:
        
        {f"Context: {context}" if context else ""}
        
        Code:
        ```python
        {code}
        ```
        
        Please provide:
        1. Code quality assessment
        2. Potential bugs or issues
        3. Performance improvements
        4. Security concerns
        5. Best practices suggestions
        
        Be concise but thorough.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating code review: {str(e)}"
    
    def generate_documentation(self, code: str) -> str:
        prompt = f"""
        Please generate comprehensive documentation for the following code:
        
        Code:
        ```python
        {code}
        ```
        
        Include:
        1. Function/class descriptions
        2. Parameter explanations
        3. Return value descriptions
        4. Usage examples
        5. Any important notes
        
        Format the documentation in markdown.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating documentation: {str(e)}"
    
    def detect_bugs(self, code: str) -> str:
        prompt = f"""
        Analyze the following code for potential bugs, errors, or issues:
        
        Code:
        ```python
        {code}
        ```
        
        Please identify:
        1. Syntax errors
        2. Logical errors
        3. Runtime errors
        4. Potential edge cases
        5. Security vulnerabilities
        
        For each issue found, provide:
        - Description of the issue
        - Potential impact
        - Suggested fix
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error detecting bugs: {str(e)}"