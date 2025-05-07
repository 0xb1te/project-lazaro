from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import ast
from dataclasses import dataclass

@dataclass
class FileAnalysis:
    """Data class for storing file analysis results."""
    file_path: str
    summary: Dict[str, Any]
    relationships: Dict[str, List[str]]
    hierarchy: Dict[str, Any]
    swot: Dict[str, List[str]]
    timestamp: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary for storage."""
        return {
            "file_path": self.file_path,
            "summary": self.summary,
            "relationships": self.relationships,
            "hierarchy": self.hierarchy,
            "swot": self.swot,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileAnalysis':
        """Create FileAnalysis from dictionary."""
        return cls(
            file_path=data["file_path"],
            summary=data["summary"],
            relationships=data["relationships"],
            hierarchy=data["hierarchy"],
            swot=data["swot"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

class FileAnalysisService:
    """Service for analyzing code files and generating documentation."""

    def __init__(self, llm_service, embedding_service):
        """Initialize with required services."""
        self.llm_service = llm_service
        self.embedding_service = embedding_service

    def analyze_file(self, file_path: str, content: str) -> FileAnalysis:
        """
        Analyze a single file and generate comprehensive documentation.
        
        Args:
            file_path: Path to the file
            content: File contents
            
        Returns:
            FileAnalysis object with analysis results
        """
        # Parse the file content
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._generate_error_analysis(file_path, "Invalid Python syntax")

        # Extract basic information
        imports = self._extract_imports(tree)
        classes = self._extract_classes(tree)
        functions = self._extract_functions(tree)

        # Generate analysis using LLM
        analysis_prompt = self._create_analysis_prompt(file_path, content, imports, classes, functions)
        analysis_result = self.llm_service.generate_response(analysis_prompt)

        # Parse LLM response into structured format
        summary = self._parse_summary(analysis_result)
        relationships = self._parse_relationships(analysis_result)
        hierarchy = self._parse_hierarchy(analysis_result)
        swot = self._parse_swot(analysis_result)

        return FileAnalysis(
            file_path=file_path,
            summary=summary,
            relationships=relationships,
            hierarchy=hierarchy,
            swot=swot
        )

    def create_index_document(self, analyses: List[FileAnalysis]) -> str:
        """
        Create an index document summarizing all analyzed files.
        
        Args:
            analyses: List of FileAnalysis objects
            
        Returns:
            Markdown formatted index document
        """
        # Group files by their position in the architecture
        architecture_groups = self._group_by_architecture(analyses)

        # Generate index content
        index_content = [
            "# Project Documentation Index\n",
            "## Project Overview\n",
            self._generate_project_overview(analyses),
            "\n## Architecture Components\n",
            self._generate_architecture_section(architecture_groups),
            "\n## File Catalog\n",
            self._generate_file_catalog(analyses),
            "\n## Key Interactions\n",
            self._generate_interactions_section(analyses),
            "\n## Getting Started\n",
            self._generate_getting_started_section(analyses)
        ]

        return "\n".join(index_content)

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

    def _create_analysis_prompt(self, file_path: str, content: str, 
                              imports: List[str], classes: List[Dict[str, Any]], 
                              functions: List[Dict[str, Any]]) -> str:
        """Create prompt for LLM analysis."""
        return f"""Analyze the following Python file and provide a comprehensive analysis:

File: {file_path}

Content:
{content}

Imports: {imports}
Classes: {classes}
Functions: {functions}

Please provide:
1. Summary:
   - Main purpose
   - Key components
   - Implementation details

2. Relationships:
   - Direct imports and dependencies
   - Modules/classes extended
   - Services provided

3. Hierarchy:
   - Parent modules/classes
   - Child components
   - Position in architecture

4. SWOT Analysis:
   - Strengths
   - Weaknesses
   - Opportunities
   - Threats

Format the response in a structured way that can be easily parsed."""

    def _parse_summary(self, analysis_result: str) -> Dict[str, Any]:
        """Parse summary section from LLM response."""
        # Implementation would parse the LLM response into structured format
        return {
            "purpose": "",
            "components": [],
            "implementation": []
        }

    def _parse_relationships(self, analysis_result: str) -> Dict[str, List[str]]:
        """Parse relationships section from LLM response."""
        return {
            "imports": [],
            "extends": [],
            "provides": []
        }

    def _parse_hierarchy(self, analysis_result: str) -> Dict[str, Any]:
        """Parse hierarchy section from LLM response."""
        return {
            "parents": [],
            "children": [],
            "position": ""
        }

    def _parse_swot(self, analysis_result: str) -> Dict[str, List[str]]:
        """Parse SWOT analysis from LLM response."""
        return {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }

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

    def _generate_project_overview(self, analyses: List[FileAnalysis]) -> str:
        """Generate project overview section."""
        # Implementation would use LLM to generate overview
        return "Project overview content..."

    def _generate_architecture_section(self, groups: Dict[str, List[FileAnalysis]]) -> str:
        """Generate architecture components section."""
        sections = []
        for layer, files in groups.items():
            if files:
                sections.append(f"\n### {layer.title()} Layer")
                for file in files:
                    sections.append(f"- {file.file_path}: {file.summary.get('purpose', '')}")
        return "\n".join(sections)

    def _generate_file_catalog(self, analyses: List[FileAnalysis]) -> str:
        """Generate file catalog section."""
        catalog = []
        for analysis in sorted(analyses, key=lambda x: x.file_path):
            catalog.append(f"\n### {analysis.file_path}")
            catalog.append(f"**Purpose:** {analysis.summary.get('purpose', '')}")
            catalog.append(f"**Position:** {analysis.hierarchy.get('position', '')}")
        return "\n".join(catalog)

    def _generate_interactions_section(self, analyses: List[FileAnalysis]) -> str:
        """Generate key interactions section."""
        # Implementation would analyze relationships between files
        return "Key interactions content..."

    def _generate_getting_started_section(self, analyses: List[FileAnalysis]) -> str:
        """Generate getting started section."""
        # Implementation would identify key entry points
        return "Getting started content..."

    def _generate_error_analysis(self, file_path: str, error: str) -> FileAnalysis:
        """Generate analysis for files with errors."""
        return FileAnalysis(
            file_path=file_path,
            summary={"purpose": f"Error: {error}"},
            relationships={},
            hierarchy={"position": "error"},
            swot={
                "strengths": [],
                "weaknesses": [error],
                "opportunities": ["Fix syntax errors"],
                "threats": ["Invalid code"]
            }
        ) 