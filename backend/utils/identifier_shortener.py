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

class IdentifierShortener(ast.NodeTransformer):
    """AST transformer to shorten identifiers"""
    
    def __init__(self, reserved_words):
        self.identifier_map = {}
        self.next_short_id = 0
        self.reserved_words = reserved_words
        super().__init__()
    
    def generate_short_identifier(self):
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
    
    def visit_Name(self, node):
        """Visit each identifier node and potentially replace it"""
        # Don't replace reserved names or special names (like __init__)
        if (node.id in self.reserved_words or 
            node.id.startswith('__') or 
            node.id.endswith('__') or
            node.id.startswith('_') or
            re.match(r'^[A-Z_]+, node.id)):  # Constants like API_KEY
            return node
        
        # Map the identifier to a shorter version
        if node.id not in self.identifier_map:
            self.identifier_map[node.id] = self.generate_short_identifier()
        
        # Create a new Name node with the shortened identifier
        new_node = ast.Name(id=self.identifier_map[node.id], ctx=node.ctx)
        # Copy the line numbers and column offset information
        ast.copy_location(new_node, node)
        
        return new_node