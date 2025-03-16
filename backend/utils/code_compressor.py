"""
Code compressor utility for reducing token consumption when indexing code files.
This module is part of the backend utilities and adds compression capabilities.
"""

import os
import re
import ast
from typing import Dict, List, Set, Tuple
import math
import logging

logger = logging.getLogger(__name__)

class CodeCompressor:
    """
    Code compressor for Python files - adapted from the TypeScript version
    """
    def __init__(self):
        self.identifier_map = {}
        self.next_short_id = 0
        self.common_patterns = {}
        self.min_pattern_length = 20
        self.reserved_words = {
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 
            'with', 'yield'
        }
    
    def generate_short_identifier(self) -> str:
        """Generate a short unique identifier"""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        id_num = self.next_short_id
        self.next_short_id += 1
        
        if id_num < len(chars):
            return chars[id_num]
        
        # For IDs beyond unique characters, combine them
        first_char = chars[math.floor(id_num / len(chars)) % len(chars)]
        second_char = chars[id_num % len(chars)]
        return first_char + second_char
    
    def compress_file(self, file_path: str) -> str:
        """Compress a source code file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        extension = os.path.splitext(file_path)[1][1:]
        return self.compress_code(source_code, extension)
    
    def compress_code(self, source_code: str, file_type: str = 'py') -> str:
        """Compress source code"""
        # Phase 1: Remove comments and unnecessary whitespace
        compressed = self.remove_comments_and_whitespace(source_code, file_type)
        
        # Phase 2: Detect repetitive patterns
        self.detect_common_patterns(compressed)
        
        # Phase 3: For Python files, use AST to shorten identifiers
        if file_type == 'py':
            compressed = self.compress_with_ast(compressed)
        
        # Phase 4: Apply pattern-based compression
        compressed = self.compress_patterns(compressed)
        
        return compressed
    
    def remove_comments_and_whitespace(self, code: str, file_type: str) -> str:
        """Remove comments and unnecessary whitespace"""
        if file_type == 'py':
            # Try to parse the code with ast to remove comments
            try:
                tree = ast.parse(code)
                # This doesn't actually remove comments, but ensures valid Python
            except SyntaxError:
                # If there's a syntax error, fall back to regex-based approach
                pass
                
            # Remove comments using regex
            # Remove single-line comments
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
            
            # Remove docstrings (simplistic approach)
            code = re.sub(r'"""[\s\S]*?"""', '', code)
            code = re.sub(r"'''[\s\S]*?'''", '', code)
            
            # Compress whitespace
            code = re.sub(r'\s+', ' ', code)
            # Remove whitespace around operators and punctuation
            code = re.sub(r'\s*([{},:;=\(\)\[\]])\s*', r'\1', code)
            # Remove whitespace at start and end of each line
            code = re.sub(r'^\s+|\s+$', '', code, flags=re.MULTILINE)
            # Remove empty lines
            code = re.sub(r'\n+', '\n', code)
            
            return code
        else:
            # Generic approach for other file types
            return code
    
    def detect_common_patterns(self, code: str) -> None:
        """Detect common patterns in code for later replacement"""
        self.common_patterns = {}
        
        # Simple approach to detect repeated substrings
        for length in range(self.min_pattern_length, 100):
            if length > len(code):
                break
                
            for i in range(len(code) - length + 1):
                pattern = code[i:i+length]
                # Ignore too simple patterns
                if not re.search(r'[a-zA-Z]', pattern):
                    continue
                
                # Count occurrences
                count = 0
                pos = 0
                while True:
                    pos = code.find(pattern, pos)
                    if pos == -1:
                        break
                    count += 1
                    pos += 1
                
                # If it appears multiple times, save it
                if count > 1:
                    self.common_patterns[pattern] = count
    
    def compress_with_ast(self, code: str) -> str:
        """Compress the code using AST analysis for Python"""
        try:
            # Make sure astor is available
            try:
                import astor
            except ImportError:
                logger.warning("astor library not found. Installing it now...")
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "astor"])
                import astor
            
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Apply the transformer to shorten identifiers
            transformer = IdentifierShortener(self.reserved_words)
            transformed_tree = transformer.visit(tree)
            
            # Use astor to convert the modified AST back to source code
            compressed_code = astor.to_source(transformed_tree)
            
            # Further compress by removing unnecessary whitespace
            compressed_code = re.sub(r'\s+', ' ', compressed_code)
            compressed_code = re.sub(r'\s*([{},:;=\(\)\[\]])\s*', r'\1', compressed_code)
            
            return compressed_code
        except Exception as e:
            # If there's any error, log it and return the original code
            logger.error(f"Error compressing code with AST: {str(e)}")
            return code
    
    def is_reserved_name(self, name: str) -> bool:
        """Check if a name is reserved in Python"""
        return name in self.reserved_words
    
    def compress_patterns(self, code: str) -> str:
        """Compress repetitive patterns by replacing them with markers"""
        # Sort patterns by (length * occurrences) to maximize space savings
        sorted_patterns = sorted(
            [(pattern, count) for pattern, count in self.common_patterns.items()
             if len(pattern) * (count - 1) > len(pattern) + 10],
            key=lambda x: len(x[0]) * x[1],
            reverse=True
        )
        
        compressed = code
        pattern_replacements = []
        
        # Replace the most relevant patterns
        for i in range(min(len(sorted_patterns), 30)):
            pattern, _ = sorted_patterns[i]
            replacement = f"##{i}##"
            pattern_replacements.append((pattern, replacement))
            compressed = compressed.replace(pattern, replacement)
        
        # Add pattern dictionary at the beginning
        dictionary = ";".join([f"{replacement}={pattern}" for pattern, replacement in pattern_replacements])
        
        return f"# dict:{dictionary}\n{compressed}"
    
    def decompress_code(self, compressed_code: str) -> str:
        """Decompress the compressed code"""
        # Extract dictionary
        dict_match = re.match(r'# dict:(.*?)\n', compressed_code)
        if not dict_match:
            return compressed_code
        
        dictionary = dict_match.group(1)
        code = re.sub(r'# dict:.*?\n', '', compressed_code)
        
        # Apply replacements in reverse order
        for item in dictionary.split(';'):
            if '=' in item:
                replacement, pattern = item.split('=', 1)
                code = code.replace(replacement, pattern)
        
        return code
    
    def get_compression_report(self, original: str, compressed: str) -> str:
        """Generate a compression report"""
        original_length = len(original)
        compressed_length = len(compressed)
        ratio = (compressed_length / original_length * 100) if original_length > 0 else 100
        
        # Calculate approximate tokens (simplified)
        original_tokens = self.estimate_tokens(original)
        compressed_tokens = self.estimate_tokens(compressed)
        token_ratio = (compressed_tokens / original_tokens * 100) if original_tokens > 0 else 100
        
        return f"""
Compression Report:
- Original size: {original_length} characters
- Compressed size: {compressed_length} characters
- Compression ratio: {ratio:.2f}%
- Estimated original tokens: {original_tokens}
- Estimated compressed tokens: {compressed_tokens}
- Token ratio: {token_ratio:.2f}%
        """
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens (very simplified)"""
        # Simple method that assumes ~4 characters per token on average
        return math.ceil(len(text) / 4)