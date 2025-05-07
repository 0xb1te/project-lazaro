from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class FileAnalysis:
    """Data class representing a file analysis result."""
    file_path: str
    summary: str
    relationships: List[Dict[str, str]]
    hierarchy: Dict[str, List[str]]
    swot: Dict[str, List[str]]
    timestamp: datetime

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
    summary: str
    relationships: List[Dict[str, str]]
    hierarchy: Dict[str, List[str]]
    swot: Dict[str, List[str]]
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert the response to a dictionary."""
        return {
            'file_path': self.file_path,
            'summary': self.summary,
            'relationships': self.relationships,
            'hierarchy': self.hierarchy,
            'swot': self.swot,
            'timestamp': self.timestamp.isoformat()
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