from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import ast
import json
from dataclasses import dataclass, asdict
import re
from collections import defaultdict
import logging

from backend.domain.port.service.llm_service import LLMService
from backend.domain.port.service.embedding_service import EmbeddingService
from backend.application.dto.file_analysis_dto import FileAnalysisRequestDTO, FileAnalysisResponseDTO, FileAnalysis

@dataclass
class CodeMetrics:
    """Data class for code quality metrics."""
    lines_of_code: int
    comment_lines: int
    complexity: int
    maintainability_index: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FileAnalysis:
    """Data class for storing file analysis results."""
    file_path: str
    summary: Dict[str, Any]
    relationships: Dict[str, List[str]]
    hierarchy: Dict[str, Any]
    swot: Dict[str, List[str]]
    metrics: CodeMetrics
    timestamp: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary for storage."""
        return {
            "file_path": self.file_path,
            "summary": self.summary,
            "relationships": self.relationships,
            "hierarchy": self.hierarchy,
            "swot": self.swot,
            "metrics": self.metrics.to_dict(),
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileAnalysis':
        """Create FileAnalysis from dictionary."""
        metrics = CodeMetrics(**data["metrics"])
        return cls(
            file_path=data["file_path"],
            summary=data["summary"],
            relationships=data["relationships"],
            hierarchy=data["hierarchy"],
            swot=data["swot"],
            metrics=metrics,
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

class FileAnalysisService:
    """Service for analyzing files and generating comprehensive documentation."""
    
    def __init__(self, llm_service: LLMService, embedding_service: EmbeddingService):
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self._index_summaries = []
        self.logger = logging.getLogger(__name__)
        
    def analyze_file(self, request: FileAnalysisRequestDTO) -> FileAnalysis:
        """
        Analyze a file and generate comprehensive documentation.
        
        Args:
            request: Analysis request containing file path and content
            
        Returns:
            Analysis response with documentation
        """
        try:
            self.logger.info(f"Starting analysis of file: {request.file_path}")
            
            # Calculate code metrics
            self.logger.debug("Calculating code metrics...")
            metrics = self._calculate_code_metrics(request.content)
            self.logger.debug(f"Code metrics calculated: LOC={metrics.lines_of_code}, Comments={metrics.comment_lines}, Complexity={metrics.complexity}")
            
            # Parse AST for Python files
            file_ext = os.path.splitext(request.file_path)[1].lower()
            ast_analysis = {}
            if file_ext == '.py':
                try:
                    self.logger.debug("Performing AST analysis for Python file...")
                    tree = ast.parse(request.content)
                    ast_analysis = {
                        'imports': self._extract_imports(tree),
                        'classes': self._extract_classes(tree),
                        'functions': self._extract_functions(tree),
                        'dependencies': self._extract_dependencies(tree)
                    }
                    self.logger.debug(f"AST analysis completed: {len(ast_analysis['imports'])} imports, {len(ast_analysis['classes'])} classes, {len(ast_analysis['functions'])} functions")
                except Exception as e:
                    self.logger.warning(f"AST analysis failed: {str(e)}")
            
            # Analyze code structure
            self.logger.debug("Analyzing code structure...")
            structure_analysis = self._analyze_code_structure(request.content, file_ext)
            self.logger.debug(f"Structure analysis completed: {len(structure_analysis['sections'])} sections, {len(structure_analysis['patterns'])} patterns identified")
            
            # Generate the analysis prompt
            self.logger.debug("Generating analysis prompt...")
            prompt = self._generate_analysis_prompt(
                request.file_path,
                request.content,
                ast_analysis,
                metrics,
                structure_analysis
            )
            self.logger.debug(f"Generated prompt of length: {len(prompt)} characters")
            
            # Get analysis from LLM
            self.logger.info("Requesting analysis from LLM...")
            analysis_result = self.llm_service.generate_with_prompt(prompt)
            self.logger.debug(f"Received LLM response of length: {len(analysis_result)} characters")
            self.logger.debug(f"Raw LLM response: {analysis_result}")
            
            # Parse the analysis result
            self.logger.debug("Parsing analysis result...")
            analysis = self._parse_analysis_result(analysis_result)
            
            # Add file path and metrics
            analysis.file_path = request.file_path
            analysis.metrics = metrics
            
            self.logger.info(f"Successfully completed analysis of {request.file_path}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {request.file_path}: {str(e)}")
            raise Exception(f"Error analyzing file: {str(e)}")
    
    def _calculate_code_metrics(self, content: str) -> CodeMetrics:
        """Calculate code quality metrics."""
        lines = content.split('\n')
        
        # Count lines
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('"""'))
        
        # Calculate complexity (simplified)
        complexity = 1
        control_flow_keywords = ['if', 'for', 'while', 'except', 'with']
        for line in lines:
            if any(keyword in line for keyword in control_flow_keywords):
                complexity += 1
                
        # Calculate maintainability index (simplified)
        # Based on: MI = 171 - 5.2 * ln(HV) - 0.23 * (G) - 16.2 * ln(LOC)
        # where HV is Halstead Volume, G is Cyclomatic Complexity, and LOC is Lines of Code
        try:
            maintainability = 171 - 5.2 * (complexity / 10) - 0.23 * complexity - 16.2 * total_lines / 100
            maintainability = max(0, min(100, maintainability))  # Clamp between 0 and 100
        except:
            maintainability = 50  # Default value if calculation fails
            
        return CodeMetrics(
            lines_of_code=total_lines,
            comment_lines=comment_lines,
            complexity=complexity,
            maintainability_index=maintainability
        )
    
    def _generate_analysis_prompt(self, file_path: str, content: str, ast_analysis: Dict[str, Any], metrics: CodeMetrics, structure_analysis: Dict[str, Any]) -> str:
        """Generate a prompt for the LLM to analyze the file."""
        file_type = os.path.splitext(file_path)[1].lower()
        
        # Add AST analysis to prompt if available
        ast_info = ""
        if ast_analysis:
            imports_str = ', '.join(ast_analysis.get('imports', []))
            classes_str = '\n'.join(f"- {cls['name']} (bases: {', '.join(cls['bases'])})" 
                                  for cls in ast_analysis.get('classes', []))
            functions_str = '\n'.join(f"- {func['name']}({', '.join(func['args'])})" 
                                    for func in ast_analysis.get('functions', []))
            dependencies_str = '\n'.join(f"- {dep['type']}: {dep.get('name', '')} {dep.get('module', '')}"
                                      for dep in ast_analysis.get('dependencies', []))
            
            ast_info = f"""
AST Analysis:
Imports: {imports_str}

Classes:
{classes_str}

Functions:
{functions_str}

Dependencies:
{dependencies_str}"""
        
        # Add structure analysis
        structure_info = ""
        if structure_analysis:
            sections_str = '\n'.join(f"- {sec['name']} (lines {sec['start']+1}-{sec['end']})" 
                                   for sec in structure_analysis['sections'])
            patterns_str = '\n'.join(f"- {pat['name']} at line {pat['line']}: {pat['context']}" 
                                   for pat in structure_analysis['patterns'])
            hotspots_str = '\n'.join(f"- Line {hot['line']}: {hot['content']}" 
                                    for hot in structure_analysis['complexity_hotspots'])
            
            structure_info = f"""
Code Structure:
Sections:
{sections_str}

Design Patterns Detected:
{patterns_str}

Complexity Hotspots:
{hotspots_str}"""
        
        # Add metrics to prompt
        metrics_info = f"""
Code Metrics:
- Lines of Code: {metrics.lines_of_code}
- Comment Lines: {metrics.comment_lines}
- Complexity: {metrics.complexity}
- Maintainability Index: {metrics.maintainability_index:.2f}/100"""

        # Add file type specific instructions
        file_type_instructions = ""
        if file_type == '.md':
            file_type_instructions = """
For Markdown documentation files:
1. Analyze the document structure (headers, sections, lists)
2. Identify key topics and concepts covered
3. Look for requirements, specifications, or design decisions
4. Note any TODOs, open questions, or decisions to be made
5. Consider the document's role in the overall project documentation
6. Look for links to other documents or components
7. Identify architectural decisions or system design elements
8. Note any implementation details or technical specifications
"""
        elif file_type in ['.py', '.js', '.ts']:
            file_type_instructions = """
For code files:
1. Identify the primary programming patterns and paradigms used
2. Note any framework-specific conventions or patterns
3. Look for error handling and validation approaches
4. Identify performance considerations
5. Note any security-related code or patterns
6. Look for configuration or environment dependencies
7. Identify test coverage and testability aspects
8. Note any technical debt or areas for improvement
"""

        prompt = f"""You are a code analysis expert. Your task is to analyze a file and output ONLY a JSON object with a specific structure.

File Information:
- Path: {file_path}
- Type: {file_type}
{ast_info}{structure_info}{metrics_info}

{file_type_instructions}

File Content:
{content}

Output a single JSON object with this exact structure. Provide DETAILED and SPECIFIC information for each section, not generic statements:

{{
    "summary": {{
        "purpose": "Write a detailed description of the file's main purpose and role",
        "components": [
            "List all major components or sections with their specific purposes",
            "Include all important elements found in the file"
        ],
        "patterns": [
            "List all design patterns, architectural patterns, or documentation patterns found",
            "Include specific examples from the file"
        ],
        "algorithms": [
            "List any algorithms, processes, or workflows described",
            "Include specific details about their implementation or description"
        ],
        "organization": "Describe how the file is structured and organized, with specific details"
    }},
    "relationships": [
        {{
            "type": "Relationship type (e.g., import, reference, implements, documents)",
            "name": "Name of the related component",
            "description": "Detailed description of how they are related"
        }}
    ],
    "hierarchy": {{
        "parents": ["List parent modules, classes, or documents that this file depends on"],
        "children": ["List components that depend on or are documented in this file"],
        "layer": "Specific architectural or documentation layer (e.g., UI, Business Logic, Data)",
        "dependencies": ["List all external dependencies with their purposes"],
        "lifecycle": "Describe how this file is used, updated, and maintained"
    }},
    "swot": {{
        "strengths": [
            "List specific strengths with concrete examples from the file",
            "Include technical merits, good practices found"
        ],
        "weaknesses": [
            "List specific areas that need improvement",
            "Include technical debt, missing elements"
        ],
        "opportunities": [
            "List specific ways the file could be enhanced",
            "Include potential new features or improvements"
        ],
        "threats": [
            "List specific risks or potential issues",
            "Include maintenance concerns, scalability issues"
        ]
    }}
}}

IMPORTANT:
1. Output ONLY the JSON object, no other text
2. Use the EXACT structure shown above
3. Ensure all JSON is properly formatted and escaped
4. Include ALL required fields (summary, relationships, hierarchy, swot)
5. Provide DETAILED, SPECIFIC information, not generic statements
6. Base all analysis on actual content found in the file
7. Include concrete examples and line references where possible
"""

        return prompt
    
    def _parse_analysis_result(self, result: str) -> FileAnalysis:
        """Parse the LLM analysis result into a FileAnalysis object."""
        try:
            self.logger.debug("Starting to parse analysis result...")
            
            # Clean up the result string
            result = result.strip()
            if not result:
                raise ValueError("Empty analysis result")
            
            # Find the JSON object
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            
            if start_idx == -1 or end_idx <= start_idx:
                self.logger.error("No valid JSON found in response")
                self.logger.debug(f"Response content: {result}")
                raise ValueError("No valid JSON found in response")
                
            json_str = result[start_idx:end_idx]
            self.logger.debug(f"Extracted JSON string: {json_str}")
            
            # Parse JSON with error handling
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                # Try to clean up common JSON formatting issues
                json_str = json_str.replace('\n', ' ').replace('\r', '')
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    self.logger.error(f"JSON parsing error after cleanup: {str(e)}")
                    self.logger.debug(f"Failed JSON string: {json_str}")
                    raise
            
            # Validate and ensure required fields
            required_fields = ['summary', 'relationships', 'hierarchy', 'swot']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.logger.error(f"Missing required fields in analysis: {missing_fields}")
                # Create default values for missing fields
                for field in missing_fields:
                    if field == 'summary':
                        data['summary'] = {
                            'purpose': 'Not specified',
                            'components': [],
                            'patterns': [],
                            'algorithms': [],
                            'organization': 'Not specified'
                        }
                    elif field == 'relationships':
                        data['relationships'] = []
                    elif field == 'hierarchy':
                        data['hierarchy'] = {
                            'parents': [],
                            'children': [],
                            'layer': 'Not specified',
                            'dependencies': [],
                            'lifecycle': 'Not specified'
                        }
                    elif field == 'swot':
                        data['swot'] = {
                            'strengths': [],
                            'weaknesses': [],
                            'opportunities': [],
                            'threats': []
                        }
            
            # Ensure relationships is a list
            if not isinstance(data['relationships'], list):
                data['relationships'] = []
            
            # Ensure all lists in summary are lists
            for key in ['components', 'patterns', 'algorithms']:
                if not isinstance(data['summary'].get(key), list):
                    data['summary'][key] = []
            
            # Ensure all lists in hierarchy are lists
            for key in ['parents', 'children', 'dependencies']:
                if not isinstance(data['hierarchy'].get(key), list):
                    data['hierarchy'][key] = []
            
            # Ensure all lists in swot are lists
            for key in ['strengths', 'weaknesses', 'opportunities', 'threats']:
                if not isinstance(data['swot'].get(key), list):
                    data['swot'][key] = []
            
            # Create FileAnalysis object
            analysis = FileAnalysis(
                file_path="",  # Will be set later
                summary=data['summary'],
                relationships=data['relationships'],
                hierarchy=data['hierarchy'],
                swot=data['swot'],
                metrics=CodeMetrics(**data.get('metrics', {
                    'lines_of_code': 0,
                    'comment_lines': 0,
                    'complexity': 0,
                    'maintainability_index': 0.0
                })),
                timestamp=datetime.utcnow()
            )
            
            self.logger.debug("Successfully created FileAnalysis object")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error parsing analysis result: {str(e)}")
            # Return a default FileAnalysis object instead of raising
            return FileAnalysis(
                file_path="",
                summary={
                    'purpose': 'Error analyzing file',
                    'components': [],
                    'patterns': [],
                    'algorithms': [],
                    'organization': 'Error during analysis'
                },
                relationships=[],
                hierarchy={
                    'parents': [],
                    'children': [],
                    'layer': 'Unknown',
                    'dependencies': [],
                    'lifecycle': 'Error during analysis'
                },
                swot={
                    'strengths': [],
                    'weaknesses': ['Error during file analysis'],
                    'opportunities': [],
                    'threats': ['Analysis failed']
                },
                metrics=CodeMetrics(
                    lines_of_code=0,
                    comment_lines=0,
                    complexity=0,
                    maintainability_index=0.0
                ),
                timestamp=datetime.utcnow()
            )
    
    def _generate_index_document(self) -> str:
        """Generate the index.txt document summarizing the codebase."""
        if not self._index_summaries:
            return ""
            
        # Generate prompt for index document
        files_summary = "\n".join(
            f"- {summary['file_path']}:\n  {summary['summary'][:200]}..."
            for summary in self._index_summaries
        )
        
        prompt = f"""Based on the following file summaries, create a comprehensive index document that includes:

1. Project Overview:
   - Overall architecture and design
   - Key components and their interactions
   - Main design patterns and principles used

2. File Catalog:
   - List of key files and their purposes
   - Important relationships between files
   - Main functionality provided by each file

3. Getting Started:
   - Recommended entry points for new developers
   - Key files to understand first
   - Important concepts and patterns to know

File Summaries:
{files_summary}

The index should be in Markdown format, be concise (2-3 pages), and provide a clear roadmap of the codebase."""

        # Get index content from LLM
        index_content = self.llm_service.generate_with_prompt(prompt)
        
        # Clear the summaries after generating index
        self._index_summaries = []
        
        return index_content

    def create_index_document(self, analyses: List[FileAnalysis]) -> str:
        """
        Create an index document summarizing all analyzed files.
        Uses vector embeddings to find relationships and organize content.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            Markdown formatted index document
        """
        self.logger.info(f"Creating index document for {len(analyses)} files")
        
        try:
            # Create embeddings for each file's content and purpose
            embeddings_map = {}
            for analysis in analyses:
                # Create a rich text representation for embedding
                content = f"""
                Purpose: {analysis.summary.get('purpose', '')}
                Components: {', '.join(analysis.summary.get('components', []))}
                Patterns: {', '.join(analysis.summary.get('patterns', []))}
                Organization: {analysis.summary.get('organization', '')}
                Layer: {analysis.hierarchy.get('layer', '')}
                """
                try:
                    embedding = self.embedding_service.get_embedding(content)
                    embeddings_map[analysis.file_path] = {
                        'embedding': embedding,
                        'analysis': analysis
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to create embedding for {analysis.file_path}: {str(e)}")
            
            # Group files by similarity using embeddings
            similarity_groups = self._group_by_similarity(embeddings_map)
            
            # Generate sections with enhanced context
            self.logger.debug("Generating index sections...")
            
            # Overview section with architectural insights
            overview = self._generate_enhanced_overview(analyses, similarity_groups)
            self.logger.debug("Generated enhanced overview")
            
            # Architecture diagram with relationship insights
            dependency_graph = self._generate_enhanced_dependency_graph(analyses, similarity_groups)
            self.logger.debug("Generated enhanced dependency graph")
            
            # Metrics with context
            metrics_summary = self._generate_metrics_summary(analyses)
            self.logger.debug("Generated metrics summary")
            
            # Enhanced file catalog with related files
            file_catalog = self._generate_enhanced_file_catalog(analyses, similarity_groups)
            self.logger.debug("Generated enhanced file catalog")
            
            # Component analysis with relationships
            component_analysis = self._generate_enhanced_component_analysis(analyses, similarity_groups)
            self.logger.debug("Generated enhanced component analysis")
            
            # Getting started guide with context
            starting_points = self._generate_enhanced_starting_points(analyses, similarity_groups)
            self.logger.debug("Generated enhanced starting points")
            
            # Detailed summaries with relationships
            detailed_summaries = self._generate_enhanced_summaries(analyses, similarity_groups)
            self.logger.debug("Generated enhanced summaries")
            
            # Combine all sections
            index_content = [
                "# Project Documentation Index\n",
                "## Project Overview\n",
                overview,
                "\n## Architecture Overview\n",
                "```mermaid\n" + dependency_graph + "\n```\n",
                "\n## Code Metrics\n",
                metrics_summary,
                "\n## File Catalog\n",
                file_catalog,
                "\n## Component Analysis\n",
                component_analysis,
                "\n## Getting Started\n",
                starting_points,
                "\n## Detailed File Summaries\n",
                detailed_summaries
            ]
            
            result = "\n".join(index_content)
            self.logger.info(f"Successfully generated enhanced index document of length: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating index document: {str(e)}")
            raise

    def _group_by_similarity(self, embeddings_map: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group files by similarity using vector embeddings."""
        groups = {}
        processed = set()
        
        try:
            # For each file, find related files based on embedding similarity
            for file_path, data in embeddings_map.items():
                if file_path in processed:
                    continue
                
                group = []
                base_embedding = data['embedding']
                
                # Compare with all other files
                for other_path, other_data in embeddings_map.items():
                    if other_path == file_path or other_path in processed:
                        continue
                    
                    try:
                        similarity = self.embedding_service.calculate_similarity(
                            base_embedding,
                            other_data['embedding']
                        )
                        
                        if similarity > 0.7:  # High similarity threshold
                            group.append({
                                'file_path': other_path,
                                'similarity': similarity,
                                'analysis': other_data['analysis']
                            })
                            processed.add(other_path)
                    except Exception as e:
                        self.logger.warning(f"Error calculating similarity for {other_path}: {str(e)}")
                
                if group:
                    groups[file_path] = sorted(group, key=lambda x: x['similarity'], reverse=True)
                processed.add(file_path)
                
            return groups
            
        except Exception as e:
            self.logger.error(f"Error grouping files by similarity: {str(e)}")
            return {}

    def _generate_enhanced_overview(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate enhanced overview with related file insights."""
        try:
            # Standard statistics
            file_types = defaultdict(int)
            total_loc = 0
            
            for analysis in analyses:
                file_type = os.path.splitext(analysis.file_path)[1].lower()
                file_types[file_type] += 1
                total_loc += analysis.metrics.lines_of_code
            
            # Group files by architectural layer with relationships
            layer_groups = defaultdict(list)
            for analysis in analyses:
                layer = analysis.hierarchy.get('layer', 'other').lower()
                layer_groups[layer].append(analysis)
            
            # Generate layer overview with relationships
            layer_overview = []
            for layer, files in layer_groups.items():
                if layer == "other":
                    continue
                    
                layer_overview.append(f"- **{layer.title()} Layer** ({len(files)} files)")
                
                # Add key files with their related files
                for file in files[:3]:
                    related = similarity_groups.get(file.file_path, [])
                    related_str = ""
                    if related:
                        related_files = [r['file_path'] for r in related[:2]]
                        related_str = f"\n    Related: {', '.join(related_files)}"
                    
                    layer_overview.append(
                        f"  - {file.file_path}: {file.summary.get('purpose', 'No purpose specified')}{related_str}"
                    )
            
            # Enhanced overview with relationships
            overview = f"""### Project Statistics
- Total Files: {len(analyses)}
- Total Lines of Code: {total_loc:,}
- File Types: {', '.join(f'{ext} ({count})' for ext, count in file_types.items())}

### Architectural Overview
{chr(10).join(layer_overview)}

### Key Design Patterns
{self._extract_design_patterns(analyses)}

### Main Technologies
{self._extract_technologies(analyses)}

### Key Relationships
{self._extract_key_relationships(analyses, similarity_groups)}
"""
            return overview
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced overview: {str(e)}")
            return "Error generating overview"

    def _extract_key_relationships(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Extract key relationships between files based on similarity."""
        try:
            relationships = []
            
            # Find the most connected files
            for file_path, related in similarity_groups.items():
                if len(related) >= 2:  # Files with multiple relationships
                    file_analysis = next((a for a in analyses if a.file_path == file_path), None)
                    if file_analysis:
                        relationships.append(f"- **{file_path}** is related to:")
                        for rel in related[:3]:  # Show top 3 relationships
                            relationships.append(
                                f"  - {rel['file_path']} (similarity: {rel['similarity']:.2f})"
                            )
            
            if not relationships:
                return "No significant relationships found"
            
            return "\n".join(relationships)
            
        except Exception as e:
            self.logger.error(f"Error extracting key relationships: {str(e)}")
            return "Error analyzing relationships"

    def _generate_enhanced_file_catalog(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate enhanced file catalog with relationship insights."""
        try:
            # Group by file type
            files_by_type = defaultdict(list)
            for analysis in analyses:
                file_type = os.path.splitext(analysis.file_path)[1].lower()
                files_by_type[file_type].append(analysis)
            
            catalog = []
            
            for file_type, files in sorted(files_by_type.items()):
                if not file_type:
                    continue
                    
                catalog.append(f"\n### {file_type.upper()[1:]} Files")
                
                for file in files:
                    # Get related files
                    related = similarity_groups.get(file.file_path, [])
                    related_str = ""
                    if related:
                        related_files = [r['file_path'] for r in related[:2]]
                        related_str = f"\n    Related Files: {', '.join(related_files)}"
                    
                    purpose = file.summary.get('purpose', 'No purpose specified')
                    components = ', '.join(file.summary.get('components', []))
                    patterns = ', '.join(file.summary.get('patterns', []))
                    
                    catalog.extend([
                        f"- **{file.file_path}**",
                        f"  - Purpose: {purpose}",
                        f"  - Components: {components}" if components else "",
                        f"  - Patterns: {patterns}" if patterns else "",
                        related_str if related_str else ""
                    ])
            
            return "\n".join(filter(None, catalog))
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced file catalog: {str(e)}")
            return "Error generating file catalog"

    def _generate_enhanced_dependency_graph(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate a Mermaid.js graph showing file dependencies."""
        graph = ["graph TD;"]
        seen_edges = set()
        
        try:
            for analysis in analyses:
                if not analysis or not isinstance(analysis.relationships, list):
                    continue
                    
                file_id = analysis.file_path.replace('/', '_').replace('.', '_')
                
                for rel in analysis.relationships:
                    if not isinstance(rel, dict):
                        continue
                        
                    rel_type = rel.get('type', '')
                    rel_name = rel.get('name', '')
                    rel_desc = rel.get('description', '')
                    
                    if rel_type and rel_type in ['import', 'extends', 'uses'] and rel_name:
                        dep_id = rel_name.replace('/', '_').replace('.', '_')
                        edge = f"{file_id}-->{dep_id}"
                        if edge not in seen_edges:
                            desc = rel_desc if rel_desc else rel_type
                            graph.append(f"    {edge}[{desc}];")
                            seen_edges.add(edge)
            
            if len(graph) == 1:  # Only has the header
                graph.append("    %% No dependencies found")
                
            return "\n".join(graph)
            
        except Exception as e:
            self.logger.error(f"Error generating dependency graph: {str(e)}")
            return "graph TD;\n    %% Error generating dependency graph"

    def _generate_metrics_summary(self, analyses: List[FileAnalysis]) -> str:
        """Generate a summary of code metrics."""
        total_loc = sum(a.metrics.lines_of_code for a in analyses)
        total_comments = sum(a.metrics.comment_lines for a in analyses)
        avg_complexity = sum(a.metrics.complexity for a in analyses) / len(analyses)
        avg_maintainability = sum(a.metrics.maintainability_index for a in analyses) / len(analyses)
        
        return f"""### Overall Metrics
- Total Lines of Code: {total_loc:,}
- Total Comment Lines: {total_comments:,}
- Comment Ratio: {(total_comments/total_loc)*100:.1f}%
- Average Complexity: {avg_complexity:.1f}
- Average Maintainability Index: {avg_maintainability:.1f}/100

### Files by Complexity
{self._generate_complexity_table(analyses)}

### Files by Maintainability
{self._generate_maintainability_table(analyses)}"""

    def _generate_complexity_table(self, analyses: List[FileAnalysis]) -> str:
        """Generate a table of files sorted by complexity."""
        sorted_files = sorted(analyses, key=lambda x: x.metrics.complexity, reverse=True)[:10]
        
        table = ["| File | Complexity | Lines of Code |", "|------|------------|---------------|"]
        for analysis in sorted_files:
            table.append(f"| {analysis.file_path} | {analysis.metrics.complexity} | {analysis.metrics.lines_of_code} |")
        
        return "\n".join(table)

    def _generate_maintainability_table(self, analyses: List[FileAnalysis]) -> str:
        """Generate a table of files sorted by maintainability index."""
        sorted_files = sorted(analyses, key=lambda x: x.metrics.maintainability_index)[:10]
        
        table = ["| File | Maintainability Index | Lines of Code |", "|------|---------------------|---------------|"]
        for analysis in sorted_files:
            table.append(f"| {analysis.file_path} | {analysis.metrics.maintainability_index:.1f} | {analysis.metrics.lines_of_code} |")
        
        return "\n".join(table)

    def _generate_development_guidelines(self, analyses: List[FileAnalysis]) -> str:
        """Generate development guidelines based on analysis."""
        # Collect common patterns and issues
        patterns = defaultdict(int)
        issues = defaultdict(int)
        
        for analysis in analyses:
            for pattern in analysis.summary.get('patterns', []):
                patterns[pattern] += 1
            for weakness in analysis.swot['weaknesses']:
                issues[weakness] += 1
        
        # Generate guidelines
        guidelines = [
            "### Coding Standards",
            "Based on the codebase analysis, follow these guidelines:",
            "",
            "#### Recommended Patterns",
            *[f"- {pattern}" for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]],
            "",
            "#### Common Issues to Avoid",
            *[f"- {issue}" for issue, count in sorted(issues.items(), key=lambda x: x[1], reverse=True)[:5]],
            "",
            "#### Best Practices",
            "1. Follow established project patterns for consistency",
            "2. Document complex logic and public interfaces",
            "3. Write unit tests for critical functionality",
            "4. Handle errors appropriately",
            "5. Keep cyclomatic complexity under control"
        ]
        
        return "\n".join(guidelines)

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend(n.name for n in node.names)
                else:
                    module = node.module if node.module else ""
                    imports.extend(f"{module}.{n.name}" for n in node.names)
        return imports

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions from AST."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                }
                classes.append(class_info)
        return classes

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions from AST."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": isinstance(node.returns, ast.Name) and node.returns.id
                }
                functions.append(func_info)
        return functions

    def _group_by_architecture(self, analyses: List[FileAnalysis]) -> Dict[str, List[FileAnalysis]]:
        """Group files by their architectural position."""
        groups = {
            "infrastructure": [],
            "domain": [],
            "application": [],
            "other": []
        }
        
        for analysis in analyses:
            position = analysis.hierarchy.get("position", "").lower()
            for key in groups:
                if key in position:
                    groups[key].append(analysis)
                    break
            else:
                groups["other"].append(analysis)
        
        return groups

    def _generate_architecture_section(self, groups: Dict[str, List[FileAnalysis]]) -> str:
        """Generate architecture components section."""
        sections = []
        for layer, files in groups.items():
            if files:
                sections.append(f"\n### {layer.title()} Layer")
                for file in files:
                    sections.append(f"- {file.file_path}: {file.summary.get('purpose', '')}")
        return "\n".join(sections)

    def _generate_interactions_section(self, analyses: List[FileAnalysis]) -> str:
        """Generate key interactions section."""
        # Implementation would analyze relationships between files
        return "Key interactions content..."

    def _generate_getting_started_section(self, analyses: List[FileAnalysis]) -> str:
        """Generate getting started section."""
        # Implementation would identify key entry points
        return "Getting started content..."

    def _analyze_code_structure(self, content: str, file_ext: str) -> Dict[str, Any]:
        """Analyze code structure based on file type."""
        structure = {
            'sections': [],
            'patterns': [],
            'complexity_hotspots': []
        }
        
        lines = content.split('\n')
        current_section = {'name': '', 'start': 0, 'end': 0, 'level': 0}
        
        # Pattern detection regexes
        patterns = {
            'singleton': r'class\s+\w+\s*\([^)]*\)\s*:\s*(?:\s*#.*)?$',
            'factory': r'create\w+|make\w+|build\w+',
            'observer': r'notify|subscribe|observer',
            'strategy': r'strategy|algorithm|policy',
            'decorator': r'@\w+',
            'dependency_injection': r'__init__.*\([^)]*\)',
        }
        
        # Analyze line by line
        for i, line in enumerate(lines):
            # Detect sections based on indentation
            indent = len(line) - len(line.lstrip())
            if line.strip() and (indent == 0 or (current_section['level'] > 0 and indent < current_section['level'])):
                if current_section['name']:
                    current_section['end'] = i
                    structure['sections'].append(current_section.copy())
                current_section = {'name': line.strip(), 'start': i, 'level': indent}
            
            # Detect patterns
            for pattern_name, regex in patterns.items():
                if re.search(regex, line):
                    structure['patterns'].append({
                        'name': pattern_name,
                        'line': i + 1,
                        'context': line.strip()
                    })
            
            # Detect complexity hotspots
            if (line.count('if ') + line.count('for ') + line.count('while ') > 1 or
                line.count('{') - line.count('}') > 1):
                structure['complexity_hotspots'].append({
                    'line': i + 1,
                    'content': line.strip()
                })
        
        # Add final section
        if current_section['name']:
            current_section['end'] = len(lines)
            structure['sections'].append(current_section)
        
        return structure

    def _extract_dependencies(self, tree: ast.AST) -> List[Dict[str, str]]:
        """Extract dependencies from AST."""
        dependencies = []
        
        for node in ast.walk(tree):
            # Import dependencies
            if isinstance(node, ast.Import):
                for name in node.names:
                    dependencies.append({
                        'type': 'import',
                        'name': name.name,
                        'alias': name.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for name in node.names:
                    dependencies.append({
                        'type': 'import_from',
                        'module': module,
                        'name': name.name,
                        'alias': name.asname
                    })
            # Class dependencies
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        dependencies.append({
                            'type': 'inherits',
                            'class': node.name,
                            'base': base.id
                        })
            # Function dependencies
            elif isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        dependencies.append({
                            'type': 'decorator',
                            'function': node.name,
                            'decorator': decorator.id
                        })
        
        return dependencies

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            import numpy as np
            # Convert to numpy arrays
            a = np.array(embedding1)
            b = np.array(embedding2)
            # Calculate cosine similarity
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

    def _extract_design_patterns(self, analyses: List[FileAnalysis]) -> str:
        """Extract common design patterns from analyses."""
        try:
            patterns = defaultdict(int)
            for analysis in analyses:
                for pattern in analysis.summary.get('patterns', []):
                    if pattern:
                        patterns[pattern] += 1
            
            if not patterns:
                return "No common design patterns identified"
            
            return "- " + "\n- ".join(f"{pattern} (used in {count} files)" 
                                    for pattern, count in sorted(patterns.items(), 
                                                            key=lambda x: x[1], 
                                                            reverse=True)[:5])
        except Exception as e:
            self.logger.error(f"Error extracting design patterns: {str(e)}")
            return "Error extracting design patterns"

    def _generate_enhanced_component_analysis(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate enhanced component analysis with relationships."""
        try:
            # Group components by type with related files
            components = defaultdict(list)
            
            for analysis in analyses:
                for component in analysis.summary.get('components', []):
                    if not component:
                        continue
                    
                    # Get related files
                    related = similarity_groups.get(analysis.file_path, [])
                    related_files = [r['file_path'] for r in related if r['similarity'] > 0.7]
                    
                    components[component].append({
                        'file': analysis.file_path,
                        'related': related_files[:2]  # Top 2 related files
                    })
            
            # Generate analysis
            sections = ["### Key Components"]
            
            for component, files in sorted(components.items()):
                if len(files) > 1:  # Only show components used in multiple files
                    sections.append(f"\n#### {component}")
                    sections.append("Files and Related Components:")
                    for file_info in files:
                        sections.append(f"- {file_info['file']}")
                        if file_info['related']:
                            sections.append(f"  Related: {', '.join(file_info['related'])}")
            
            if len(sections) == 1:
                sections.append("\nNo significant components identified")
            
            return "\n".join(sections)
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced component analysis: {str(e)}")
            return "Error generating component analysis"

    def _generate_enhanced_starting_points(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate enhanced getting started section with entry points and relationships."""
        try:
            # Find potential entry points
            entry_points = []
            core_files = []
            utilities = []
            
            for analysis in analyses:
                file_path = analysis.file_path.lower()
                if "main" in file_path or "app" in file_path or "index" in file_path:
                    entry_points.append(analysis)
                elif analysis.metrics.complexity < 10 and "util" in file_path:
                    utilities.append(analysis)
                elif len(analysis.relationships) > 3:  # Files with many relationships
                    core_files.append(analysis)
            
            content = [
                "### Recommended Entry Points",
                "Start with these files to understand the project structure:",
            ]
            
            # Add entry points with related files
            if entry_points:
                for ep in entry_points:
                    related = similarity_groups.get(ep.file_path, [])
                    related_str = ""
                    if related:
                        related_files = [r['file_path'] for r in related[:2]]
                        related_str = f"\n    Related Files: {', '.join(related_files)}"
                    content.append(f"- **{ep.file_path}**: {ep.summary.get('purpose', 'Main entry point')}{related_str}")
            
            # Add core files with relationships
            content.extend([
                "\n### Core Files",
                "These files contain core functionality and important patterns:"
            ])
            
            for cf in sorted(core_files, key=lambda x: len(x.relationships), reverse=True)[:3]:
                related = similarity_groups.get(cf.file_path, [])
                related_str = ""
                if related:
                    related_files = [r['file_path'] for r in related[:2]]
                    related_str = f"\n    Related Files: {', '.join(related_files)}"
                content.append(f"- **{cf.file_path}**: {cf.summary.get('purpose', 'Core functionality')}{related_str}")
            
            # Add key concepts with context
            content.extend([
                "\n### Key Concepts",
                self._extract_key_concepts(analyses)
            ])
            
            return "\n".join(content)
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced starting points: {str(e)}")
            return "Error generating starting points"

    def _extract_key_concepts(self, analyses: List[FileAnalysis]) -> str:
        """Extract key concepts that developers should understand."""
        try:
            concepts = set()
            
            for analysis in analyses:
                # Add architectural concepts
                if analysis.hierarchy.get('layer'):
                    concepts.add(f"**{analysis.hierarchy['layer']}** architectural layer")
                
                # Add design patterns
                for pattern in analysis.summary.get('patterns', []):
                    if pattern:  # Skip empty patterns
                        concepts.add(f"**{pattern}** design pattern")
                
                # Add important components
                for component in analysis.summary.get('components', []):
                    if component:  # Skip empty components
                        concepts.add(f"**{component}** component")
            
            if not concepts:
                return "No key concepts identified"
            
            return "Important concepts to understand:\n- " + "\n- ".join(sorted(concepts))
            
        except Exception as e:
            self.logger.error(f"Error extracting key concepts: {str(e)}")
            return "Error extracting key concepts"

    def _generate_enhanced_summaries(self, analyses: List[FileAnalysis], similarity_groups: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate enhanced detailed file summaries with relationships."""
        try:
            summaries = []
            
            for analysis in sorted(analyses, key=lambda x: x.file_path):
                # Get related files
                related = similarity_groups.get(analysis.file_path, [])
                related_str = ""
                if related:
                    related_files = [f"- {r['file_path']} (similarity: {r['similarity']:.2f})" 
                                   for r in related[:3]]
                    related_str = "\n\n#### Related Files\n" + "\n".join(related_files)
                
                summaries.extend([
                    f"\n### {analysis.file_path}",
                    "\n#### Purpose",
                    analysis.summary.get('purpose', 'No purpose specified'),
                    
                    "\n#### Implementation",
                    "- " + "\n- ".join(analysis.summary.get('patterns', ['No patterns specified'])),
                    
                    related_str,
                    
                    "\n#### SWOT Analysis",
                    "\nStrengths:",
                    "- " + "\n- ".join(analysis.swot.get('strengths', ['None specified'])),
                    "\nWeaknesses:",
                    "- " + "\n- ".join(analysis.swot.get('weaknesses', ['None specified'])),
                    "\nOpportunities:",
                    "- " + "\n- ".join(analysis.swot.get('opportunities', ['None specified'])),
                    "\nThreats:",
                    "- " + "\n- ".join(analysis.swot.get('threats', ['None specified'])),
                    
                    "\n#### Relationships",
                    self._format_relationships(analysis.relationships)
                ])
            
            return "\n".join(summaries)
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced summaries: {str(e)}")
            return "Error generating summaries"

    def _format_relationships(self, relationships: List[Dict[str, str]]) -> str:
        """Format relationships into readable text."""
        try:
            if not relationships:
                return "No relationships defined"
            
            formatted = []
            for rel in relationships:
                rel_type = rel.get('type', '').title()
                name = rel.get('name', '')
                desc = rel.get('description', '')
                
                if rel_type and name:
                    formatted.append(f"- {rel_type}: **{name}**")
                    if desc:
                        formatted.append(f"  - {desc}")
            
            return "\n".join(formatted) if formatted else "No relationships defined"
            
        except Exception as e:
            self.logger.error(f"Error formatting relationships: {str(e)}")
            return "Error formatting relationships" 