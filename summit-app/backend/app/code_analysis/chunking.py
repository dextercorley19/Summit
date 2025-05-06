import ast
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CodeChunk:
    def __init__(self, content: str, start_line: int, end_line: int, type: str):
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.type = type  # 'class', 'function', 'module_level'
        
    def __repr__(self):
        return f"CodeChunk({self.type}, lines {self.start_line}-{self.end_line})"

def get_node_source(source_lines: List[str], node: ast.AST) -> str:
    """Get the source code for an AST node."""
    start = node.lineno - 1  # Convert to 0-based indexing
    end = node.end_lineno if hasattr(node, 'end_lineno') else start + 1
    return '\n'.join(source_lines[start:end])

def is_empty_or_whitespace(lines: List[str]) -> bool:
    """Check if a list of lines contains only whitespace or is empty."""
    return all(not line.strip() for line in lines)

def chunk_code(source_code: str, max_chunk_size: int = 1000) -> List[CodeChunk]:
    """
    Split Python code into logical chunks based on class and function definitions.
    Similar to how Cursor handles code analysis.
    """
    chunks = []
    source_lines = source_code.splitlines()
    
    # Handle empty input
    if not source_lines or is_empty_or_whitespace(source_lines):
        return []
    
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logger.error(f"Syntax error in code: {e}")
        # If parsing fails, return the whole file as one chunk
        return [CodeChunk(source_code, 1, len(source_lines), 'module_level')]
    
    # Track which lines are part of a class or function
    covered_lines = set()
    
    # First, handle classes and their methods
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_source = get_node_source(source_lines, node)
            class_lines = set(range(node.lineno, node.end_lineno + 1))
            covered_lines.update(class_lines)
            
            # Add the class definition and any class-level code
            chunks.append(CodeChunk(
                class_source,
                node.lineno,
                node.end_lineno,
                'class'
            ))
            
            # Handle methods separately if the class is too large
            if len(class_source.splitlines()) > max_chunk_size:
                for sub_node in ast.walk(node):
                    if isinstance(sub_node, ast.FunctionDef):
                        method_source = get_node_source(source_lines, sub_node)
                        method_lines = set(range(sub_node.lineno, sub_node.end_lineno + 1))
                        covered_lines.update(method_lines)
                        
                        chunks.append(CodeChunk(
                            method_source,
                            sub_node.lineno,
                            sub_node.end_lineno,
                            'function'
                        ))
    
    # Then handle standalone functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not any(
            node.lineno >= chunk.start_line and node.end_lineno <= chunk.end_line
            for chunk in chunks
        ):
            func_source = get_node_source(source_lines, node)
            func_lines = set(range(node.lineno, node.end_lineno + 1))
            covered_lines.update(func_lines)
            
            chunks.append(CodeChunk(
                func_source,
                node.lineno,
                node.end_lineno,
                'function'
            ))
    
    # Finally, handle module-level code
    current_chunk_start = 0
    current_chunk_lines = []
    
    for i, line in enumerate(source_lines):
        if i + 1 not in covered_lines:  # Convert to 1-based line numbers
            current_chunk_lines.append(line)
            
            # If chunk gets too large or we reach the end, create a new chunk
            if len(current_chunk_lines) >= max_chunk_size or i == len(source_lines) - 1:
                if current_chunk_lines and not is_empty_or_whitespace(current_chunk_lines):
                    chunks.append(CodeChunk(
                        '\n'.join(current_chunk_lines),
                        current_chunk_start + 1,
                        current_chunk_start + len(current_chunk_lines),
                        'module_level'
                    ))
                current_chunk_lines = []
                current_chunk_start = i + 1
    
    # Add any remaining module-level code
    if current_chunk_lines and not is_empty_or_whitespace(current_chunk_lines):
        chunks.append(CodeChunk(
            '\n'.join(current_chunk_lines),
            current_chunk_start + 1,
            current_chunk_start + len(current_chunk_lines),
            'module_level'
        ))
    
    # Sort chunks by line number
    chunks.sort(key=lambda x: x.start_line)
    return chunks

def get_chunk_context(chunk: CodeChunk, all_chunks: List[CodeChunk]) -> str:
    """
    Get contextual information about a chunk's location in the codebase.
    """
    context = []
    
    # Add information about chunk type and size
    context.append(f"{chunk.type.title()} with {len(chunk.content.splitlines())} lines")
    
    # Find containing class if this is a method
    if chunk.type == 'function':
        containing_class = None
        for other_chunk in all_chunks:
            if (other_chunk.type == 'class' and
                other_chunk.start_line <= chunk.start_line and
                other_chunk.end_line >= chunk.end_line):
                containing_class = other_chunk
                break
        
        if containing_class:
            # Extract class name from the class definition
            try:
                class_tree = ast.parse(containing_class.content)
                for node in ast.walk(class_tree):
                    if isinstance(node, ast.ClassDef):
                        context.insert(0, f"Method in class {node.name}")  # Insert at beginning
                        break
            except Exception as e:
                logger.error(f"Error parsing class content: {e}")
    
    # Add information about dependencies
    imports = []
    for line in chunk.content.splitlines():
        if line.strip().startswith(('import ', 'from ')):
            imports.append(line.strip())
    if imports:
        context.append("Dependencies: " + ", ".join(imports))
    
    return " | ".join(context)
