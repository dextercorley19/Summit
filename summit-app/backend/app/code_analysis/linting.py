import os
import pylint.lint
from pylint.reporters import JSONReporter
from io import StringIO
import json
from typing import Dict, List, Tuple, Any
import sys
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

class CodeAnalyzer:
    def __init__(self, repo_path: str, mcp_server: MCPServerStdio):
        self.repo_path = repo_path
        self.mcp_server = mcp_server
        self.agent = Agent(model='openai:gpt-4.1', mcp_servers=[mcp_server])
        
    async def analyze_python_files(self) -> Dict[str, Any]:
        """
        Analyzes all Python files in the repository using Pylint and MCP agents.
        Returns a dictionary containing scores and AI-powered insights.
        """
        python_files = self._find_python_files()
        analysis_results = {}
        
        # First get basic Pylint scores
        for file_path in python_files:
            score = self._run_pylint(file_path)
            analysis_results[file_path] = {
                'lint_score': score,
                'insights': None,
                'suggestions': None
            }
        
        # Then use MCP agent for deeper analysis
        async with self.agent.run_mcp_servers():
            for file_path in python_files:
                relative_path = os.path.relpath(file_path, self.repo_path)
                
                # Get AI insights about the code
                insights_prompt = f"Analyze the code quality and structure of {relative_path}. Focus on: 1) Code organization 2) Potential bugs 3) Performance issues"
                insights_result = await self.agent.run(insights_prompt)
                
                # Get specific improvement suggestions
                suggestions_prompt = f"Suggest specific improvements for {relative_path} that would make it more maintainable and efficient. Be concrete and actionable."
                suggestions_result = await self.agent.run(suggestions_prompt)
                
                analysis_results[file_path].update({
                    'insights': insights_result.output,
                    'suggestions': suggestions_result.output
                })
            
        return analysis_results
    
    def _find_python_files(self) -> List[str]:
        """
        Recursively finds all Python files in the repository.
        """
        python_files = []
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def _run_pylint(self, file_path: str) -> float:
        """
        Runs Pylint on a single file and returns the score.
        """
        output = StringIO()
        reporter = JSONReporter(output)
        
        # Run Pylint with custom reporter
        pylint.lint.Run(
            [file_path],
            reporter=reporter,
            do_exit=False
        )
        
        # Parse the JSON output
        output_str = output.getvalue()
        if not output_str:
            return 10.0  # Perfect score if no issues found
            
        try:
            lint_results = json.loads(output_str)
            # Calculate score based on number and severity of issues
            return self._calculate_score(lint_results)
        except json.JSONDecodeError:
            return 0.0  # Return 0 if there was an error parsing results
    
    def _calculate_score(self, lint_results: List[Dict]) -> float:
        """
        Calculates a score from 0-10 based on Pylint results.
        """
        if not lint_results:
            return 10.0
            
        # Weight different issue types
        weights = {
            'error': 1.0,
            'warning': 0.5,
            'convention': 0.1,
            'refactor': 0.3,
            'info': 0.1
        }
        
        total_weight = sum(weights[issue['type']] for issue in lint_results)
        max_deduction = 10.0
        score = max(0, 10.0 - (total_weight * max_deduction / 10))
        
        return round(score, 2)
    
    async def get_repository_analysis(self) -> Tuple[float, Dict[str, Any]]:
        """
        Returns the overall repository analysis including scores and AI insights.
        """
        analysis_results = await self.analyze_python_files()
        if not analysis_results:
            return 0.0, {}
            
        # Calculate overall score from lint scores
        lint_scores = [result['lint_score'] for result in analysis_results.values()]
        avg_score = sum(lint_scores) / len(lint_scores)
        
        # Get repository-wide insights using MCP agent
        async with self.agent.run_mcp_servers():
            repo_analysis_prompt = "Analyze the overall repository structure and provide insights about: 1) Code organization 2) Common patterns 3) Areas for improvement"
            repo_analysis = await self.agent.run(repo_analysis_prompt)
            
            for file_path, results in analysis_results.items():
                results['repo_context'] = repo_analysis.output
        
        return round(avg_score, 2), analysis_results
