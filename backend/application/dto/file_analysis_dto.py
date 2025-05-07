from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class CodeMetrics:
    """Data class representing code quality metrics."""
    lines_of_code: int
    comment_lines: int
    complexity: int
    maintainability_index: float

    def to_dict(self) -> Dict:
        """Convert metrics to a dictionary."""
        return {
            'lines_of_code': self.lines_of_code,
            'comment_lines': self.comment_lines,
            'complexity': self.complexity,
            'maintainability_index': self.maintainability_index
        }

@dataclass
class FileAnalysis:
    """Data class representing a file analysis result."""
    file_path: str
    summary: Dict[str, any]  # Enhanced summary with components, patterns, etc.
    relationships: List[Dict[str, str]]  # Enhanced relationships with more types
    hierarchy: Dict[str, List[str]]  # Enhanced hierarchy with lifecycle info
    swot: Dict[str, List[str]]  # Detailed SWOT analysis
    metrics: CodeMetrics
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert analysis to a dictionary."""
        return {
            'file_path': self.file_path,
            'summary': self.summary,
            'relationships': self.relationships,
            'hierarchy': self.hierarchy,
            'swot': self.swot,
            'metrics': self.metrics.to_dict(),
            'timestamp': self.timestamp.isoformat()
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

@dataclass
class FileAnalysisRequestDTO:
    """Data class representing a file analysis request."""
    file_path: str
    content: str
    conversation_id: Optional[str] = None

@dataclass
class FileAnalysisResponseDTO:
    """Data class representing a file analysis response."""
    file_path: str
    summary: Dict[str, any]
    relationships: List[Dict[str, str]]
    hierarchy: Dict[str, List[str]]
    swot: Dict[str, List[str]]
    metrics: CodeMetrics
    timestamp: datetime
    index_content: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert response to a dictionary."""
        return {
            'file_path': self.file_path,
            'summary': self.summary,
            'relationships': self.relationships,
            'hierarchy': self.hierarchy,
            'swot': self.swot,
            'metrics': self.metrics.to_dict(),
            'timestamp': self.timestamp.isoformat(),
            'index_content': self.index_content
        }

@dataclass
class IndexDocumentDTO:
    """Data class representing an index document."""
    content: str
    conversation_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert the index document to a dictionary."""
        return {
            'content': self.content,
            'conversation_id': self.conversation_id
        } 