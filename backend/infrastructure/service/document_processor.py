# src/infrastructure/service/document_processor.py
import os
import io
import zipfile
import tempfile
from typing import List, Dict, Any, Union, Tuple, Optional
from pathlib import Path
import shutil
import json
import re

from backend.domain.port.service.document_processor_service import DocumentProcessorService
from backend.domain.model.document import Document
from backend.domain.model.document_chunk import DocumentChunk

class DocumentProcessor(DocumentProcessorService):
    """
    Implementation of the DocumentProcessorService interface.
    Handles loading, processing and chunking various document types.
    """
    
    def __init__(self, upload_folder: str, storage_dir: str = None):
        """
        Initialize the document processor.
        
        Args:
            upload_folder: Path to temporary upload folder
            storage_dir: Path to permanent storage directory (defaults to upload_folder if not specified)
        """
        self.upload_folder = upload_folder
        self.storage_dir = storage_dir if storage_dir is not None else upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def process_file(self, file_path: Union[str, Path], file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process a file from disk and extract its content.
        
        Args:
            file_path: Path to the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            A Document object with the processed content
        """
        file_path = str(file_path)  # Ensure string path
        
        # Default metadata
        if metadata is None:
            metadata = {}
        
        # Determine file type
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Process based on file type
        if file_ext == '.zip':
            return self._process_zip_file(file_path, file_name, metadata)
        elif file_ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.html', '.css', '.md', '.txt']:
            return self._process_text_file(file_path, file_name, metadata)
        else:
            # For unsupported types, just store as plain text
            return self._process_generic_file(file_path, file_name, metadata)
    
    def process_binary(self, binary_data: Union[bytes, io.BytesIO], file_name: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process binary data and return a Document.
        
        Args:
            binary_data: Binary content of the file
            file_name: Name of the file
            metadata: Additional metadata for the document
            
        Returns:
            A Document object with the processed content
        """
        # Save to temporary file first
        if isinstance(binary_data, io.BytesIO):
            binary_data = binary_data.getvalue()
        
        temp_file_path = os.path.join(self.upload_folder, file_name)
        
        try:
            with open(temp_file_path, 'wb') as f:
                f.write(binary_data)
            
            # Process the file
            document = self.process_file(temp_file_path, file_name, metadata)
            
            return document
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def chunk_document(self, document: Document, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[DocumentChunk]:
        """
        Split a document into chunks for efficient processing and retrieval.
        
        Args:
            document: The document to chunk
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks in characters
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        content = document.content
        
        # Skip chunking for very short documents
        if len(content) <= chunk_size:
            chunk = DocumentChunk(
                content=content,
                metadata=document.metadata.copy(),
                document_id=document.id
            )
            chunks.append(chunk)
            return chunks
        
        # Chunk by splitting on newlines when possible
        start = 0
        while start < len(content):
            end = start + chunk_size
            
            if end >= len(content):
                # Last chunk
                chunk_text = content[start:]
            else:
                # Try to find a newline to break on
                newline_pos = content.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1  # Include the newline
                
                chunk_text = content[start:end]
            
            # Create chunk with metadata
            chunk_metadata = document.metadata.copy()
            chunk_metadata["chunk_index"] = len(chunks)
            chunk_metadata["char_start"] = start
            chunk_metadata["char_end"] = end
            
            chunk = DocumentChunk(
                content=chunk_text,
                metadata=chunk_metadata,
                document_id=document.id
            )
            chunks.append(chunk)
            
            # Move start position for the next chunk, considering overlap
            start = max(start, end - chunk_overlap)
        
        return chunks
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get a list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return [
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs',
            '.html', '.css', '.md', '.txt', '.json', '.xml', '.zip'
        ]
    
    # Private helper methods
    
    def _get_language_config(self, extension: str) -> Dict[str, Any]:
        """Get language-specific configuration for file analysis."""
        configs = {
            # JavaScript
            '.js': {
                'language': 'javascript',
                'patterns': {
                    'imports': [
                        (r'^import\s+.*from\s+[\'"].*[\'"]', 'import'),
                        (r'^require\([\'"].*[\'"]\)', 'require')
                    ],
                    'exports': [
                        (r'^export\s+.*', 'export'),
                        (r'module\.exports\s*=.*', 'module.exports')
                    ],
                    'functions': [
                        (r'function\s+\w+\s*\(.*\)', 'function'),
                        (r'\w+\s*=\s*function\s*\(.*\)', 'function'),
                        (r'\w+\s*=\s*\(.*\)\s*=>', 'arrow function'),
                        (r'const\s+\w+\s*=\s*\(.*\)\s*=>', 'arrow function')
                    ],
                    'classes': [
                        (r'^class\s+\w+', 'class')
                    ]
                },
                'frameworks': ['React', 'Vue', 'Angular', 'Express']
            },
            # Python
            '.py': {
                'language': 'python',
                'patterns': {
                    'imports': [
                        (r'^import\s+.*', 'import'),
                        (r'^from\s+.*import\s+.*', 'from import')
                    ],
                    'exports': [
                        (r'^__all__\s*=.*', '__all__')
                    ],
                    'functions': [
                        (r'^def\s+\w+\s*\(.*\)', 'function'),
                        (r'^async\s+def\s+\w+\s*\(.*\)', 'async function')
                    ],
                    'classes': [
                        (r'^class\s+\w+.*:', 'class')
                    ]
                },
                'frameworks': ['Django', 'Flask', 'FastAPI', 'SQLAlchemy']
            },
            # TypeScript
            '.ts': {
                'language': 'typescript',
                'patterns': {
                    'imports': [
                        (r'^import\s+.*from\s+[\'"].*[\'"]', 'import')
                    ],
                    'exports': [
                        (r'^export\s+.*', 'export')
                    ],
                    'functions': [
                        (r'function\s+\w+\s*\(.*\)', 'function'),
                        (r'\w+\s*=\s*function\s*\(.*\)', 'function'),
                        (r'\w+\s*=\s*\(.*\)\s*=>', 'arrow function'),
                        (r'const\s+\w+\s*=\s*\(.*\)\s*=>', 'arrow function')
                    ],
                    'classes': [
                        (r'^class\s+\w+', 'class'),
                        (r'^interface\s+\w+', 'interface')
                    ]
                },
                'frameworks': ['Angular', 'NestJS', 'Next.js']
            },
            # HTML
            '.html': {
                'language': 'html',
                'patterns': {
                    'imports': [
                        (r'<link.*rel=[\'"]stylesheet[\'"].*>', 'stylesheet'),
                        (r'<script.*src=.*>', 'script')
                    ],
                    'components': [
                        (r'<\w+[-\w]*.*>', 'custom element')
                    ]
                },
                'frameworks': ['React', 'Vue', 'Angular', 'Svelte']
            },
            # CSS/SCSS
            '.css': {
                'language': 'css',
                'patterns': {
                    'imports': [
                        (r'^@import\s+.*', 'import')
                    ],
                    'components': [
                        (r'^\.[\\w-]+\s*{', 'class'),
                        (r'^#[\\w-]+\s*{', 'id'),
                        (r'@media\s+.*{', 'media query')
                    ]
                }
            },
            # Java
            '.java': {
                'language': 'java',
                'patterns': {
                    'imports': [
                        (r'^import\s+.*', 'import')
                    ],
                    'functions': [
                        (r'(public|private|protected)\s+\w+\s+\w+\s*\(.*\)', 'method')
                    ],
                    'classes': [
                        (r'^(public|private|protected)?\s*class\s+\w+', 'class'),
                        (r'^(public|private|protected)?\s*interface\s+\w+', 'interface')
                    ]
                },
                'frameworks': ['Spring', 'Hibernate', 'Jakarta EE']
            }
        }
        
        # Add common patterns for all languages
        common_patterns = {
            'todos': [
                (r'TODO[\s:].*', 'todo'),
                (r'FIXME[\s:].*', 'fixme'),
                (r'HACK[\s:].*', 'hack'),
                (r'NOTE[\s:].*', 'note')
            ],
            'comments': [
                (r'^\s*#.*', 'hash comment'),
                (r'^\s*//.*', 'line comment'),
                (r'/\*.*?\*/', 'block comment')
            ]
        }
        
        config = configs.get(extension, {
            'language': 'generic',
            'patterns': {}
        })
        
        # Add common patterns to all languages
        config['patterns'].update(common_patterns)
        return config

    def _analyze_file_content(self, content: str, extension: str) -> Dict[str, Any]:
        """Analyze file content using language-specific patterns."""
        config = self._get_language_config(extension)
        analysis = {
            'language': config['language'],
            'findings': {}
        }
        
        # Analyze content using patterns
        for category, patterns in config['patterns'].items():
            matches = []
            for pattern, pattern_type in patterns:
                found = re.finditer(pattern, content, re.MULTILINE)
                for match in found:
                    matches.append({
                        'type': pattern_type,
                        'text': match.group().strip(),
                        'line': content.count('\n', 0, match.start()) + 1
                    })
            if matches:
                analysis['findings'][category] = matches
        
        # Check for frameworks
        if 'frameworks' in config:
            detected_frameworks = []
            for framework in config['frameworks']:
                if framework.lower() in content.lower():
                    detected_frameworks.append(framework)
            if detected_frameworks:
                analysis['frameworks'] = detected_frameworks
        
        # Add basic metrics
        lines = content.split('\n')
        analysis.update({
            'metrics': {
                'total_lines': len(lines),
                'non_empty_lines': len([l for l in lines if l.strip()]),
                'size_bytes': len(content),
                'has_unicode': any(ord(c) > 127 for c in content)
            }
        })
        
        return analysis

    def _process_text_file(self, file_path: str, file_name: str, metadata: Dict[str, Any]) -> Document:
        """Process a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Get file extension
            extension = os.path.splitext(file_name)[1].lower()
            
            # Analyze file content
            analysis = self._analyze_file_content(content, extension)
            
            # Update metadata with analysis results
            metadata.update({
                "file_type": "text",
                "filename": file_name,
                "extension": extension,
                "language": analysis['language'],
                "metrics": analysis['metrics'],
                "analysis": analysis
            })
            
            # Create document
            return Document(
                filename=file_name,
                content=content,
                type="file",
                metadata=metadata
            )
        except Exception as e:
            # Log error and return empty document
            print(f"Error processing text file {file_name}: {e}")
            return Document(
                filename=file_name,
                content=f"Error processing file: {str(e)}",
                type="file",
                metadata=metadata
            )
    
    def _process_zip_file(self, file_path: str, file_name: str, metadata: Dict[str, Any]) -> Document:
        """Process a ZIP archive with improved nested folder handling and detailed analysis."""
        temp_dir = tempfile.mkdtemp(dir=self.upload_folder)
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Get list of all files in the ZIP
                file_list = zip_ref.namelist()
                
                # Create a mapping of file paths to their content
                file_contents = {}
                file_metadata = {}
                
                # First pass: extract all files
                for file_path in file_list:
                    if file_path.endswith('/'):  # Skip directories
                        continue
                        
                    # Get file extension
                    ext = os.path.splitext(file_path)[1].lower()
                    
                    # Skip unwanted paths and files
                    if any(pattern in file_path for pattern in [
                        '__pycache__/', '.git/', 'node_modules/', 
                        'venv/', '.env/', 'build/', 'dist/',
                        'bin/', 'obj/'
                    ]):
                        continue
                    
                    # Extract file to temp directory
                    zip_ref.extract(file_path, temp_dir)
                    full_path = os.path.join(temp_dir, file_path)
                    
                    # Only process if file exists and is readable
                    if os.path.exists(full_path) and os.path.isfile(full_path):
                        try:
                            # Special handling for JavaScript files
                            if ext == '.js':
                                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                                    content = f.read()
                                    
                                # Extract JS-specific metadata
                                imports = []
                                exports = []
                                functions = []
                                classes = []
                                
                                lines = content.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    # Detect imports
                                    if line.startswith('import ') or line.startswith('require('):
                                        imports.append(line)
                                    # Detect exports
                                    elif line.startswith('export '):
                                        exports.append(line)
                                    # Detect functions (basic detection)
                                    elif 'function ' in line or '=>' in line:
                                        functions.append(line)
                                    # Detect classes
                                    elif line.startswith('class '):
                                        classes.append(line)
                                
                                file_contents[file_path] = content
                                file_metadata[file_path] = {
                                    'size': len(content),
                                    'lines': len(lines),
                                    'extension': ext,
                                    'is_binary': False,
                                    'language': 'javascript',
                                    'imports': imports,
                                    'exports': exports,
                                    'functions': functions,
                                    'classes': classes,
                                    'is_module': bool(imports or exports),
                                    'is_component': any('React' in imp or 'Vue' in imp or 'Component' in content for imp in imports)
                                }
                            else:
                                # Regular text file handling
                                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                                    content = f.read()
                                    file_contents[file_path] = content
                                    
                                    # Basic file analysis
                                    file_metadata[file_path] = {
                                        'size': len(content),
                                        'lines': content.count('\n') + 1,
                                        'extension': ext,
                                        'is_binary': False
                                    }
                        except UnicodeError:
                            # Mark as binary if can't read as text
                            file_metadata[file_path] = {
                                'size': os.path.getsize(full_path),
                                'lines': 0,
                                'extension': ext,
                                'is_binary': True
                            }
                
                # Generate detailed analysis
                analysis = self._analyze_zip_contents(file_contents, file_metadata)
                
                # Build the document content
                all_text = []
                
                # Add analysis summary
                all_text.append("# ZIP Archive Analysis\n\n")
                all_text.append(f"## Overview\n")
                all_text.append(f"- Total Files: {len(file_contents)}\n")
                all_text.append(f"- Total Size: {sum(m['size'] for m in file_metadata.values())} bytes\n")
                all_text.append(f"- File Types: {', '.join(sorted(set(m['extension'] for m in file_metadata.values())))}\n\n")
                
                # Add JavaScript files summary if present
                js_files = [(f, m) for f, m in file_metadata.items() if m['extension'] == '.js']
                if js_files:
                    all_text.append("## JavaScript Files Analysis\n")
                    for js_file, meta in js_files:
                        all_text.append(f"\n### {js_file}\n")
                        all_text.append(f"- Lines: {meta['lines']}\n")
                        all_text.append(f"- Size: {meta['size']} bytes\n")
                        if 'imports' in meta:
                            all_text.append(f"- Imports: {len(meta['imports'])}\n")
                            for imp in meta['imports']:
                                all_text.append(f"  - {imp}\n")
                        if 'exports' in meta:
                            all_text.append(f"- Exports: {len(meta['exports'])}\n")
                            for exp in meta['exports']:
                                all_text.append(f"  - {exp}\n")
                        if 'functions' in meta:
                            all_text.append(f"- Functions: {len(meta['functions'])}\n")
                        if 'classes' in meta:
                            all_text.append(f"- Classes: {len(meta['classes'])}\n")
                        if meta.get('is_module'):
                            all_text.append("- Type: Module\n")
                        if meta.get('is_component'):
                            all_text.append("- Type: UI Component\n")
                    all_text.append("\n")
                
                # Add file structure
                all_text.append("## File Structure\n")
                for file_path in sorted(file_contents.keys()):
                    meta = file_metadata[file_path]
                    all_text.append(f"- {file_path}\n")
                    all_text.append(f"  - Size: {meta['size']} bytes\n")
                    all_text.append(f"  - Lines: {meta['lines']}\n")
                    all_text.append(f"  - Type: {'Binary' if meta['is_binary'] else 'Text'}\n")
                
                # Add detailed analysis
                all_text.append("\n## Detailed Analysis\n")
                all_text.append(analysis)
                
                # Add file contents
                all_text.append("\n## File Contents\n")
                for file_path, content in sorted(file_contents.items()):
                    all_text.append(f"\n### {file_path}\n")
                    all_text.append("```\n")
                    all_text.append(content)
                    all_text.append("\n```\n")
                
                # Update metadata
                metadata.update({
                    "file_type": "zip",
                    "filename": file_name,
                    "file_count": len(file_contents),
                    "analysis": analysis,
                    "js_files": [f for f, m in file_metadata.items() if m['extension'] == '.js']
                })
                
                # Create document
                return Document(
                    filename=file_name,
                    content=''.join(all_text),
                    type="zip",
                    metadata=metadata
                )
        except Exception as e:
            # Log error and return empty document
            print(f"Error processing ZIP file {file_name}: {e}")
            return Document(
                filename=file_name,
                content=f"Error processing ZIP file: {str(e)}",
                type="zip",
                metadata=metadata
            )
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _analyze_zip_contents(self, file_contents: Dict[str, str], file_metadata: Dict[str, Dict]) -> str:
        """Analyze the contents of a ZIP file and generate a detailed report."""
        analysis = []
        
        # Calculate overall statistics
        total_files = len(file_contents)
        total_size = sum(m['size'] for m in file_metadata.values())
        total_lines = sum(m['lines'] for m in file_metadata.values())
        
        # Group files by extension
        extension_groups = {}
        for file_path, meta in file_metadata.items():
            ext = meta['extension']
            if ext not in extension_groups:
                extension_groups[ext] = []
            extension_groups[ext].append(file_path)
        
        # Generate analysis
        analysis.append("### Project Statistics\n")
        analysis.append(f"- Total Files: {total_files}\n")
        analysis.append(f"- Total Size: {total_size} bytes\n")
        analysis.append(f"- Total Lines: {total_lines}\n")
        
        # File type distribution
        analysis.append("\n### File Type Distribution\n")
        for ext, files in sorted(extension_groups.items()):
            analysis.append(f"- {ext}: {len(files)} files\n")
        
        # Generate file summaries
        analysis.append("\n### File Summaries\n")
        for file_path, content in sorted(file_contents.items()):
            meta = file_metadata[file_path]
            if not meta['is_binary']:
                summary = self._generate_file_summary(file_path, content, meta)
                analysis.append(f"\n#### {file_path}\n")
                analysis.append(summary)
        
        # Identify potential code files
        code_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs', '.html', '.css'}
        code_files = [f for f, m in file_metadata.items() if m['extension'] in code_extensions]
        
        if code_files:
            analysis.append("\n### Code Analysis\n")
            analysis.append("#### Potential Code Files\n")
            for file_path in sorted(code_files):
                meta = file_metadata[file_path]
                analysis.append(f"- {file_path}\n")
                analysis.append(f"  - Lines: {meta['lines']}\n")
                analysis.append(f"  - Size: {meta['size']} bytes\n")
        
        # Identify large files
        large_files = [(f, m['size']) for f, m in file_metadata.items() if m['size'] > 1000000]  # > 1MB
        if large_files:
            analysis.append("\n### Large Files\n")
            for file_path, size in sorted(large_files, key=lambda x: x[1], reverse=True):
                analysis.append(f"- {file_path}: {size} bytes\n")
        
        # Identify binary files
        binary_files = [f for f, m in file_metadata.items() if m['is_binary']]
        if binary_files:
            analysis.append("\n### Binary Files\n")
            for file_path in sorted(binary_files):
                meta = file_metadata[file_path]
                analysis.append(f"- {file_path}: {meta['size']} bytes\n")
        
        return ''.join(analysis)
    
    def _generate_file_summary(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a summary for a single file using AI analysis."""
        summary = []
        
        # Basic file information
        summary.append(f"- **Type**: {metadata['extension']}\n")
        summary.append(f"- **Size**: {metadata['size']} bytes\n")
        summary.append(f"- **Lines**: {metadata['lines']}\n")
        
        # File content analysis
        try:
            # Analyze file content
            if metadata['extension'] in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs'}:
                # Code file analysis
                summary.append("\n#### Code Analysis\n")
                summary.append(self._analyze_code_file(content, metadata['extension']))
            elif metadata['extension'] in {'.md', '.txt', '.rst'}:
                # Documentation analysis
                summary.append("\n#### Content Analysis\n")
                summary.append(self._analyze_documentation(content))
            elif metadata['extension'] in {'.json', '.xml', '.yaml', '.yml'}:
                # Data file analysis
                summary.append("\n#### Data Structure Analysis\n")
                summary.append(self._analyze_data_file(content, metadata['extension']))
            
            # Add file purpose and key findings
            summary.append("\n#### Key Findings\n")
            summary.append(self._analyze_file_purpose(content, metadata['extension']))
            
        except Exception as e:
            summary.append(f"\nError analyzing file: {str(e)}\n")
        
        return ''.join(summary)
    
    def _analyze_code_file(self, content: str, extension: str) -> str:
        """Analyze a code file and return insights."""
        analysis = []
        
        # Basic code metrics
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        comment_lines = [l for l in lines if l.strip().startswith(('#', '//', '/*', '*', '--'))]
        
        analysis.append(f"- **Code Lines**: {len(non_empty_lines)}\n")
        analysis.append(f"- **Comment Lines**: {len(comment_lines)}\n")
        analysis.append(f"- **Comment Ratio**: {len(comment_lines)/len(non_empty_lines)*100:.1f}%\n")
        
        # Language-specific analysis
        if extension == '.py':
            analysis.append("\n#### Python-specific Analysis\n")
            # Count imports
            imports = [l for l in lines if l.strip().startswith(('import ', 'from '))]
            analysis.append(f"- **Imports**: {len(imports)}\n")
            # Count functions
            functions = [l for l in lines if l.strip().startswith('def ')]
            analysis.append(f"- **Functions**: {len(functions)}\n")
            # Count classes
            classes = [l for l in lines if l.strip().startswith('class ')]
            analysis.append(f"- **Classes**: {len(classes)}\n")
        
        return ''.join(analysis)
    
    def _analyze_documentation(self, content: str) -> str:
        """Analyze documentation content."""
        analysis = []
        
        # Basic metrics
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        analysis.append(f"- **Total Lines**: {len(lines)}\n")
        analysis.append(f"- **Non-empty Lines**: {len(non_empty_lines)}\n")
        
        # Section analysis
        sections = [l for l in lines if l.strip().startswith('#')]
        analysis.append(f"- **Sections**: {len(sections)}\n")
        
        return ''.join(analysis)
    
    def _analyze_data_file(self, content: str, extension: str) -> str:
        """Analyze a data file (JSON, XML, YAML)."""
        analysis = []
        
        try:
            if extension == '.json':
                import json
                data = json.loads(content)
                analysis.append(self._analyze_json_structure(data))
            elif extension in {'.yaml', '.yml'}:
                import yaml
                data = yaml.safe_load(content)
                analysis.append(self._analyze_yaml_structure(data))
            elif extension == '.xml':
                import xml.etree.ElementTree as ET
                root = ET.fromstring(content)
                analysis.append(self._analyze_xml_structure(root))
        except Exception as e:
            analysis.append(f"Error analyzing data file: {str(e)}\n")
        
        return ''.join(analysis)
    
    def _analyze_json_structure(self, data: Any, depth: int = 0) -> str:
        """Analyze JSON structure recursively."""
        analysis = []
        
        if isinstance(data, dict):
            analysis.append(f"- **Object** with {len(data)} keys\n")
            for key, value in data.items():
                analysis.append(f"  - {key}: {self._analyze_json_structure(value, depth + 1)}")
        elif isinstance(data, list):
            analysis.append(f"- **Array** with {len(data)} items\n")
            if data:
                analysis.append(f"  - First item type: {type(data[0]).__name__}\n")
        else:
            analysis.append(f"- **{type(data).__name__}**\n")
        
        return ''.join(analysis)
    
    def _analyze_yaml_structure(self, data: Any) -> str:
        """Analyze YAML structure."""
        return self._analyze_json_structure(data)  # YAML can be treated similarly to JSON
    
    def _analyze_xml_structure(self, root: Any) -> str:
        """Analyze XML structure."""
        analysis = []
        
        def analyze_node(node: Any, depth: int = 0) -> None:
            analysis.append(f"{'  ' * depth}- {node.tag}\n")
            for child in node:
                analyze_node(child, depth + 1)
        
        analyze_node(root)
        return ''.join(analysis)
    
    def _analyze_file_purpose(self, content: str, extension: str) -> str:
        """Analyze the purpose and key aspects of a file."""
        analysis = []
        
        # Basic content analysis
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        # Look for common patterns
        if extension in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs'}:
            # Code file patterns
            if any('def main(' in l for l in lines):
                analysis.append("- Appears to be a main entry point\n")
            if any('class ' in l for l in lines):
                analysis.append("- Contains class definitions\n")
            if any('def ' in l for l in lines):
                analysis.append("- Contains function definitions\n")
        elif extension in {'.md', '.txt', '.rst'}:
            # Documentation patterns
            if any('# ' in l for l in lines):
                analysis.append("- Contains section headers\n")
            if any('```' in l for l in lines):
                analysis.append("- Contains code blocks\n")
        elif extension in {'.json', '.xml', '.yaml', '.yml'}:
            # Data file patterns
            analysis.append("- Contains structured data\n")
        
        # Add SWOT Analysis
        analysis.append("\n#### SWOT Analysis\n")
        swot = self._generate_swot_analysis(content, extension)
        analysis.extend(swot)
        
        return ''.join(analysis)
    
    def _generate_swot_analysis(self, content: str, extension: str) -> List[str]:
        """Generate a detailed SWOT analysis for the file."""
        analysis = []
        
        # Common patterns for all file types
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        comment_lines = [l for l in lines if l.strip().startswith(('#', '//', '/*', '*', '--'))]
        
        # Strengths
        analysis.append("**Strengths:**\n")
        strengths = []
        
        # Code quality indicators
        if extension in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs'}:
            if len(comment_lines) > len(non_empty_lines) * 0.2:  # Good documentation
                strengths.append("- Well-documented code\n")
            if any('test' in l.lower() for l in lines):  # Test presence
                strengths.append("- Contains test cases\n")
            if any('TODO' in l or 'FIXME' in l for l in lines):  # Development tracking
                strengths.append("- Tracks development tasks\n")
        
        # Documentation quality
        elif extension in {'.md', '.txt', '.rst'}:
            if len(lines) > 50:  # Substantial documentation
                strengths.append("- Comprehensive documentation\n")
            if any('```' in l for l in lines):  # Code examples
                strengths.append("- Includes code examples\n")
            if any('## ' in l for l in lines):  # Good structure
                strengths.append("- Well-structured content\n")
        
        # Data file quality
        elif extension in {'.json', '.xml', '.yaml', '.yml'}:
            if len(non_empty_lines) > 10:  # Substantial data
                strengths.append("- Contains substantial data\n")
            if any('"description"' in l or 'description:' in l for l in lines):  # Metadata
                strengths.append("- Includes metadata\n")
        
        if not strengths:
            strengths.append("- File serves its intended purpose\n")
        analysis.extend(strengths)
        
        # Weaknesses
        analysis.append("\n**Weaknesses:**\n")
        weaknesses = []
        
        if extension in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs'}:
            if len(comment_lines) < len(non_empty_lines) * 0.1:  # Poor documentation
                weaknesses.append("- Limited documentation\n")
            if len(non_empty_lines) > 500:  # Very long file
                weaknesses.append("- File might be too long\n")
            if any('TODO' in l or 'FIXME' in l for l in lines):  # Unfinished work
                weaknesses.append("- Contains unfinished work\n")
        
        elif extension in {'.md', '.txt', '.rst'}:
            if len(lines) < 10:  # Minimal documentation
                weaknesses.append("- Limited documentation\n")
            if not any('## ' in l for l in lines):  # Poor structure
                weaknesses.append("- Lacks clear structure\n")
        
        elif extension in {'.json', '.xml', '.yaml', '.yml'}:
            if len(non_empty_lines) < 5:  # Minimal data
                weaknesses.append("- Contains minimal data\n")
            if not any('"description"' in l or 'description:' in l for l in lines):  # No metadata
                weaknesses.append("- Lacks metadata\n")
        
        if not weaknesses:
            weaknesses.append("- No significant weaknesses identified\n")
        analysis.extend(weaknesses)
        
        # Opportunities
        analysis.append("\n**Opportunities:**\n")
        opportunities = []
        
        if extension in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs'}:
            if len(comment_lines) < len(non_empty_lines) * 0.2:
                opportunities.append("- Could benefit from more documentation\n")
            if not any('test' in l.lower() for l in lines):
                opportunities.append("- Could add test cases\n")
            if len(non_empty_lines) > 500:
                opportunities.append("- Could be split into smaller modules\n")
        
        elif extension in {'.md', '.txt', '.rst'}:
            if not any('```' in l for l in lines):
                opportunities.append("- Could add code examples\n")
            if not any('## ' in l for l in lines):
                opportunities.append("- Could improve structure with headers\n")
        
        elif extension in {'.json', '.xml', '.yaml', '.yml'}:
            if not any('"description"' in l or 'description:' in l for l in lines):
                opportunities.append("- Could add metadata\n")
            if len(non_empty_lines) < 10:
                opportunities.append("- Could be expanded with more data\n")
        
        if not opportunities:
            opportunities.append("- No significant opportunities identified\n")
        analysis.extend(opportunities)
        
        # Threats
        analysis.append("\n**Threats:**\n")
        threats = []
        
        if extension in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.cs'}:
            if any('TODO' in l or 'FIXME' in l for l in lines):
                threats.append("- Contains unfinished work that needs attention\n")
            if len(non_empty_lines) > 1000:
                threats.append("- Large file size may impact maintainability\n")
        
        elif extension in {'.md', '.txt', '.rst'}:
            if len(lines) < 5:
                threats.append("- Minimal documentation may lead to misunderstandings\n")
        
        elif extension in {'.json', '.xml', '.yaml', '.yml'}:
            if len(non_empty_lines) < 3:
                threats.append("- Minimal data may not be sufficient for intended purpose\n")
        
        if not threats:
            threats.append("- No significant threats identified\n")
        analysis.extend(threats)
        
        return analysis
    
    def _process_generic_file(self, file_path: str, file_name: str, metadata: Dict[str, Any]) -> Document:
        """Process a generic file as text."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except:
            # If can't read as text, use placeholder
            content = f"[Binary file: {file_name}]"
        
        # Update metadata
        metadata.update({
            "file_type": "generic",
            "filename": file_name,
            "extension": os.path.splitext(file_name)[1].lower()
        })
        
        # Create document
        return Document(
            filename=file_name,
            content=content,
            type="file",
            metadata=metadata
        )
    
    def _ensure_conversation_structure(self, conversation_id: str) -> str:
        """
        Ensure the conversation directory exists with the required structure.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The path to the conversation directory
        """
        # Construct the conversation directory path
        conversation_dir = os.path.join(self.storage_dir, 'conversations', conversation_id)
        
        # Create the directory if it doesn't exist
        os.makedirs(conversation_dir, exist_ok=True)
        
        # Ensure conversation.json exists with empty messages array
        json_path = os.path.join(conversation_dir, 'conversation.json')
        if not os.path.exists(json_path):
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write('{"messages": []}')
        
        return conversation_dir
    
    def save_conversation_data(self, conversation_id: str, conversation_data: Dict[str, Any]) -> None:
        """
        Save conversation data to conversation.json.
        
        Args:
            conversation_id: The ID of the conversation
            conversation_data: The data for conversation.json
        """
        try:
            # Ensure directory exists
            conversation_dir = self._ensure_conversation_structure(conversation_id)
            
            # Save conversation.json
            json_path = os.path.join(conversation_dir, 'conversation.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving conversation data for {conversation_id}: {str(e)}")
            raise
    
    def save_index_file(self, conversation_id: str, index_content: str) -> None:
        """
        Save index.md file for a conversation.
        This is only created when a document is uploaded.
        
        Args:
            conversation_id: The ID of the conversation
            index_content: The content for index.md
        """
        try:
            # Ensure directory exists
            conversation_dir = self._ensure_conversation_structure(conversation_id)
            
            # Save index.md
            index_path = os.path.join(conversation_dir, 'index.md')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
                
        except Exception as e:
            print(f"Error saving index file for {conversation_id}: {str(e)}")
            raise
    
    def get_conversation_data(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation data from conversation.json.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The conversation data
        """
        try:
            conversation_dir = os.path.join(self.storage_dir, 'conversations', conversation_id)
            
            if not os.path.exists(conversation_dir):
                raise FileNotFoundError(f"Conversation directory not found: {conversation_dir}")
            
            # Read conversation.json
            json_path = os.path.join(conversation_dir, 'conversation.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            return conversation_data
            
        except Exception as e:
            print(f"Error reading conversation data for {conversation_id}: {str(e)}")
            raise
    
    def get_index_content(self, conversation_id: str) -> Optional[str]:
        """
        Get the content of index.md if it exists.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            The content of index.md if it exists, None otherwise
        """
        try:
            index_path = os.path.join(self.storage_dir, 'conversations', conversation_id, 'index.md')
            
            if not os.path.exists(index_path):
                return None
            
            with open(index_path, 'r', encoding='utf-8') as f:
                return f.read()
            
        except Exception as e:
            print(f"Error reading index file for {conversation_id}: {str(e)}")
            raise
    
    def delete_conversation(self, conversation_id: str) -> None:
        """
        Delete a conversation and ALL of its associated files and contents.
        This will completely remove the conversation directory and everything inside it.
        
        Args:
            conversation_id: The ID of the conversation to delete
        """
        try:
            # Construct the conversation directory path
            conversation_dir = os.path.join(self.storage_dir, 'conversations', conversation_id)
            
            # Check if directory exists
            if os.path.exists(conversation_dir):
                # First, verify the contents that will be deleted
                contents = os.listdir(conversation_dir)
                print(f"Deleting conversation directory: {conversation_dir}")
                print(f"Contents to be deleted: {contents}")
                
                # Delete the entire directory and ALL of its contents
                shutil.rmtree(conversation_dir)
                
                # Verify deletion
                if os.path.exists(conversation_dir):
                    raise Exception(f"Failed to delete conversation directory: {conversation_dir}")
                    
                print(f"Successfully deleted conversation directory and all contents: {conversation_dir}")
            else:
                print(f"Conversation directory not found: {conversation_dir}")
                
        except Exception as e:
            print(f"Error deleting conversation {conversation_id}: {str(e)}")
            raise 
