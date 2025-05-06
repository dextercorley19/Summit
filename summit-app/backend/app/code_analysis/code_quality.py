from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Tuple
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
from .chunking import chunk_code, get_chunk_context, CodeChunk

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChunkAnalysis(BaseModel):
    content_type: str  # 'class', 'function', 'module_level'
    context: str
    quality_score: float
    insights: str
    suggestions: str

class FileAnalysis(BaseModel):
    lint_score: float
    chunks: Dict[str, ChunkAnalysis]  # chunk_id -> analysis
    recent_changes: str
    insights: str
    suggestions: str
    repo_context: str

class CodeQualityResponse(BaseModel):
    overall_score: float
    file_analyses: Dict[str, FileAnalysis]
    summary: str

async def get_recent_python_files(token: str) -> List[Dict[str, str]]:
    """Get list of repositories accessible to the user."""
    try:
        # Set up MCP server with GitHub token
        mcp_server = MCPServerStdio(
            command='docker',
            args=[
                'run',
                '-i',
                '--rm',
                '-e',
                'GITHUB_PERSONAL_ACCESS_TOKEN',
                'ghcr.io/github/github-mcp-server',
            ],
            env={'GITHUB_PERSONAL_ACCESS_TOKEN': token}
        )
        
        agent = Agent(model='openai:gpt-4.1', mcp_servers=[mcp_server])
        
        async with agent.run_mcp_servers():
            repos_prompt = """List all repositories I have access to.
            Format each line as: owner/repo
            Only include repositories I can read.
            Sort by last modified date (newest first).
            Limit to 10 repositories."""
            
            repos_result = await agent.run(repos_prompt)
            
            repositories = []
            for line in repos_result.output.split('\n'):
                if '/' in line:
                    owner, repo = line.strip().split('/')
                    repositories.append({
                        "full_name": f"{owner}/{repo}",
                        "owner": owner,
                        "name": repo
                    })
            
            return repositories[:10]
    except Exception as e:
        logger.error(f"Error listing repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing repositories: {str(e)}")

async def analyze_chunk(agent: Agent, chunk: CodeChunk, file_path: str, owner: str, repo: str, all_chunks: List[CodeChunk]) -> ChunkAnalysis:
    """Analyze a single code chunk."""
    chunk_context = get_chunk_context(chunk, all_chunks)
    
    analysis_prompt = f"""Analyze this {chunk.type} from {file_path} in {owner}/{repo}:

    Context: {chunk_context}
    
    Code:
    {chunk.content}
    
    Provide a brief analysis (max 200 words) with:
    1. Quality score (0-10)
    2. Key insights about the code
    3. Specific improvement suggestions
    
    Format as:
    Score: [number]
    Insights: [text]
    Suggestions: [text]"""
    
    try:
        analysis_result = await agent.run(analysis_prompt)
        analysis_text = analysis_result.output
        
        # Parse the response
        import re
        score_match = re.search(r'Score:.*?(\d+(?:\.\d+)?)', analysis_text)
        insights_match = re.search(r'Insights:(.*?)(?:Suggestions:|$)', analysis_text, re.DOTALL)
        suggestions_match = re.search(r'Suggestions:(.*?)$', analysis_text, re.DOTALL)
        
        return ChunkAnalysis(
            content_type=chunk.type,
            context=chunk_context,
            quality_score=min(max(float(score_match.group(1)) if score_match else 5.0, 0.0), 10.0),
            insights=insights_match.group(1).strip() if insights_match else 'No insights provided.',
            suggestions=suggestions_match.group(1).strip() if suggestions_match else 'No suggestions provided.'
        )
    except Exception as e:
        logger.error(f"Error analyzing chunk: {str(e)}")
        return ChunkAnalysis(
            content_type=chunk.type,
            context=chunk_context,
            quality_score=5.0,
            insights=f"Error analyzing code: {str(e)}",
            suggestions="Try analyzing again later."
        )

async def analyze_file(agent: Agent, owner: str, repo: str, file_info: Tuple[str, str]) -> Dict[str, Any]:
    """Analyze a file using smart code chunking."""
    file_path, content = file_info
    
    try:
        # Split the file into logical chunks
        chunks = chunk_code(content)
        
        # Analyze each chunk
        chunk_analyses = {}
        for i, chunk in enumerate(chunks):
            if i > 0:  # Add delay between chunks
                await asyncio.sleep(1)
            
            chunk_id = f"{chunk.type}_{chunk.start_line}_{chunk.end_line}"
            chunk_analyses[chunk_id] = await analyze_chunk(agent, chunk, file_path, owner, repo, chunks)
        
        # Calculate overall file score
        chunk_scores = [analysis.quality_score for analysis in chunk_analyses.values()]
        overall_score = sum(chunk_scores) / len(chunk_scores) if chunk_scores else 5.0
        
        # Get file-level insights
        await asyncio.sleep(1)  # Rate limit before file analysis
        file_prompt = f"""Summarize the overall quality of {file_path} based on its components:

        {len(chunks)} chunks analyzed:
        {', '.join(f"{c.type} (lines {c.start_line}-{c.end_line})" for c in chunks)}
        
        Provide:
        1. Recent changes and their impact
        2. Overall code insights
        3. High-level improvement suggestions
        4. How this file fits in the repository
        
        Keep response under 200 words."""
        
        file_analysis = await agent.run(file_prompt)
        analysis_text = file_analysis.output
        
        # Parse file-level analysis
        import re
        changes_match = re.search(r'Recent changes:(.*?)(?:Insights:|$)', analysis_text, re.DOTALL)
        insights_match = re.search(r'Insights:(.*?)(?:Suggestions:|$)', analysis_text, re.DOTALL)
        suggestions_match = re.search(r'Suggestions:(.*?)(?:Context:|$)', analysis_text, re.DOTALL)
        context_match = re.search(r'Context:(.*?)$', analysis_text, re.DOTALL)
        
        return {
            'lint_score': overall_score,
            'chunks': chunk_analyses,
            'recent_changes': changes_match.group(1).strip() if changes_match else 'No recent changes noted.',
            'insights': insights_match.group(1).strip() if insights_match else 'No insights provided.',
            'suggestions': suggestions_match.group(1).strip() if suggestions_match else 'No suggestions provided.',
            'repo_context': context_match.group(1).strip() if context_match else 'No context provided.'
        }
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {str(e)}")
        return {
            'lint_score': 5.0,
            'chunks': {},
            'recent_changes': f"Error analyzing file: {str(e)}",
            'insights': 'Analysis failed.',
            'suggestions': 'Try analyzing again later.',
            'repo_context': 'Unable to determine.'
        }

@router.get("/analyze/{owner}/{repo}", response_model=CodeQualityResponse)
async def analyze_code_quality(owner: str, repo: str):
    """
    Analyzes the code quality of recently modified files in a GitHub repository using MCP agents.
    Uses smart code chunking to handle large files efficiently.
    """
    logger.info(f"Starting analysis for repository: {owner}/{repo}")
    
    try:
        # Set up MCP server with GitHub token
        token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
        if not token:
            logger.error("GitHub token not found in environment variables")
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        logger.debug("Setting up MCP server")
        mcp_server = MCPServerStdio(
            command='docker',
            args=[
                'run',
                '-i',
                '--rm',
                '-e',
                'GITHUB_PERSONAL_ACCESS_TOKEN',
                'ghcr.io/github/github-mcp-server',
            ],
            env={'GITHUB_PERSONAL_ACCESS_TOKEN': token}
        )
        
        agent = Agent(model='openai:gpt-4.1', mcp_servers=[mcp_server])
        
        logger.info("Starting code analysis")
        async with agent.run_mcp_servers():
            # Get recently modified repository files
            python_files = await get_recent_python_files(token)
            if not python_files:
                logger.warning("No Python files modified in the last 30 days")
                return CodeQualityResponse(
                    overall_score=0.0,
                    file_analyses={},
                    summary="No Python files have been modified in the last 30 days."
                )
            
            # Analyze each file
            analysis_results = {}
            for file_info in python_files:
                try:
                    logger.debug(f"Analyzing file: {file_info['full_name']}")
                    if analysis_results:  # Add delay between files
                        await asyncio.sleep(2)
                    analysis_results[file_info['full_name']] = await analyze_file(agent, owner, repo, (file_info['full_name'], file_info['content']))
                except Exception as e:
                    logger.error(f"Error analyzing file {file_info['full_name']}: {str(e)}")
                    continue
            
            # Get overall repository analysis
            if analysis_results:
                await asyncio.sleep(2)  # Rate limit before final analysis
                repo_prompt = f"""Summarize the recent changes (last 30 days) in {owner}/{repo}.
                Focus on the {len(analysis_results)} most recently modified files.
                Keep your response under 200 words.
                Include:
                1. Key trends in recent changes
                2. Overall code quality direction
                3. Main areas for improvement"""
                
                repo_analysis = await agent.run(repo_prompt)
                
                # Calculate overall score
                overall_score = sum(result['lint_score'] for result in analysis_results.values()) / len(analysis_results)
            else:
                overall_score = 0.0
                repo_analysis = type('obj', (object,), {'output': 'No files analyzed.'})
            
            # Convert results to response format
            file_analyses = {
                path: FileAnalysis(
                    lint_score=results['lint_score'],
                    chunks=results['chunks'],
                    recent_changes=results['recent_changes'],
                    insights=results['insights'],
                    suggestions=results['suggestions'],
                    repo_context=results['repo_context']
                )
                for path, results in analysis_results.items()
            }
            
            # Generate summary
            summary = _generate_summary(overall_score, file_analyses, repo_analysis.output)
            
            logger.info("Analysis completed successfully")
            return CodeQualityResponse(
                overall_score=overall_score,
                file_analyses=file_analyses,
                summary=summary
            )
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing repository: {str(e)}"
        )

def _generate_summary(overall_score: float, file_analyses: Dict[str, FileAnalysis], repo_analysis: str) -> str:
    """
    Generates a human-readable summary of the code quality analysis.
    """
    if not file_analyses:
        return "No Python files have been modified in the last 30 days."
    
    num_files = len(file_analyses)
    perfect_files = sum(1 for analysis in file_analyses.values() if analysis.lint_score >= 9.5)
    problem_files = sum(1 for analysis in file_analyses.values() if analysis.lint_score < 7.0)
    
    summary = f"Analysis of {num_files} recently modified Python files:\n"
    summary += f"- Overall code quality score: {overall_score:.1f}/10\n"
    summary += f"- {perfect_files} files have excellent quality (score >= 9.5)\n"
    summary += f"- {problem_files} files need attention (score < 7.0)\n\n"
    
    # Add chunk-level insights
    for file_path, analysis in file_analyses.items():
        summary += f"\n{file_path}:\n"
        summary += f"- Overall file score: {analysis.lint_score:.1f}/10\n"
        
        # Group chunks by type
        chunks_by_type = {}
        for chunk_id, chunk in analysis.chunks.items():
            if chunk.content_type not in chunks_by_type:
                chunks_by_type[chunk.content_type] = []
            chunks_by_type[chunk.content_type].append((chunk_id, chunk))
        
        # Report on each type
        for chunk_type, chunks in chunks_by_type.items():
            type_score = sum(c[1].quality_score for c in chunks) / len(chunks)
            summary += f"  {chunk_type.title()}: {len(chunks)} analyzed, avg score {type_score:.1f}/10\n"
        
        # Add key insights
        if analysis.insights:
            summary += f"  Key insight: {analysis.insights.split('.')[0]}.\n"
        if analysis.suggestions:
            summary += f"  Main suggestion: {analysis.suggestions.split('.')[0]}.\n"
    
    summary += f"\nRecent Development Analysis:\n{repo_analysis}\n"
    
    return summary
