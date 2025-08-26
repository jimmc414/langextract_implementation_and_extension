"""
Resolver module for reference and relationship resolution.

This module provides functionality to:
- Resolve pronouns and references to their antecedents
- Identify relationships between extracted entities
- Disambiguate partial names and abbreviations
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import difflib
import re

from langextract import data


class ReferenceType(Enum):
    """Types of references that can be resolved."""
    PRONOUN = "pronoun"
    ABBREVIATION = "abbreviation"
    ALIAS = "alias"
    COREFERENCE = "coreference"
    PARTIAL = "partial"


class RelationshipType(Enum):
    """Types of relationships between entities."""
    EMPLOYMENT = "employment"
    LOCATION = "location"
    TEMPORAL = "temporal"
    FINANCIAL = "financial"
    OWNERSHIP = "ownership"
    FAMILIAL = "familial"
    ASSOCIATION = "association"


@dataclass
class Reference:
    """Represents a reference relationship between extractions."""
    source_text: str
    target_text: str
    reference_type: ReferenceType
    confidence: float = 0.0
    distance: int = 0
    source_id: Optional[str] = None
    target_id: Optional[str] = None


@dataclass 
class Relationship:
    """Represents a relationship between two entities."""
    source_text: str
    target_text: str
    relationship_type: RelationshipType
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)
    entity1_id: Optional[str] = None
    entity2_id: Optional[str] = None
    evidence: Optional[str] = None


class ReferenceResolver:
    """
    Resolves references like pronouns, abbreviations, and partial names
    to their full entities.
    """
    
    # Common pronouns by type
    PERSON_PRONOUNS = {
        'he', 'him', 'his', 'she', 'her', 'hers',
        'He', 'Him', 'His', 'She', 'Her', 'Hers'
    }
    
    ORGANIZATION_PRONOUNS = {
        'it', 'its', 'It', 'Its', 'they', 'them', 
        'their', 'theirs', 'They', 'Them', 'Their', 'Theirs'
    }
    
    PLURAL_PRONOUNS = {
        'they', 'them', 'their', 'theirs',
        'They', 'Them', 'Their', 'Theirs'
    }
    
    def __init__(self, fuzzy_threshold: float = 0.8, max_distance: int = 500):
        """
        Initialize the reference resolver.
        
        Args:
            fuzzy_threshold: Minimum similarity for fuzzy matching (0-1)
            max_distance: Maximum character distance for reference resolution
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.max_distance = max_distance
        self.resolved_references: List[Reference] = []
    
    def resolve_references(
        self,
        extractions: List[data.Extraction],
        text: str
    ) -> List[data.Extraction]:
        """
        Resolve all references in the extractions.
        
        Args:
            extractions: List of extractions to process
            text: Original document text
            
        Returns:
            List of extractions with resolved references
        """
        # Clear previous resolutions
        self.resolved_references = []
        
        # Sort extractions by position for proper resolution order
        sorted_extractions = self._sort_by_position(extractions)
        
        # Process each extraction
        for i, extraction in enumerate(sorted_extractions):
            if self._is_reference(extraction):
                # Find what this references
                referent = self._find_referent(
                    extraction, 
                    sorted_extractions[:i],  # Only look at previous extractions
                    text
                )
                
                if referent:
                    # Add reference information
                    self._add_reference_info(extraction, referent)
                    
                    # Record the reference
                    ref = Reference(
                        source_text=extraction.extraction_text,
                        target_text=referent.extraction_text,
                        reference_type=self._get_reference_type(extraction),
                        confidence=self._calculate_confidence(extraction, referent),
                        distance=self._calculate_distance(extraction, referent),
                        source_id=extraction.extraction_id or str(i),
                        target_id=referent.extraction_id or str(sorted_extractions.index(referent))
                    )
                    self.resolved_references.append(ref)
        
        return sorted_extractions
    
    def _sort_by_position(self, extractions: List[data.Extraction]) -> List[data.Extraction]:
        """Sort extractions by their position in the text."""
        def get_position(ext):
            if ext.char_interval and hasattr(ext.char_interval, 'start') and ext.char_interval.start is not None:
                return ext.char_interval.start
            return float('inf')
        
        return sorted(extractions, key=get_position)
    
    def _is_reference(self, extraction: data.Extraction) -> bool:
        """Check if an extraction is likely a reference."""
        text = extraction.extraction_text
        
        # Check for pronouns
        if text in self.PERSON_PRONOUNS or text in self.ORGANIZATION_PRONOUNS:
            return True
        
        # Check for abbreviations (2-5 uppercase letters)
        if text.isupper() and 2 <= len(text) <= 5 and text.isalpha():
            return True
        
        # Check for partial names (single word that could be surname)
        if (extraction.extraction_class == 'person' and 
            ' ' not in text and 
            len(text) > 2):
            return True
        
        # Check for definite articles suggesting reference
        if text.lower().startswith(('the ', 'this ', 'that ', 'these ', 'those ')):
            return True
        
        return False
    
    def _get_reference_type(self, extraction: data.Extraction) -> ReferenceType:
        """Determine the type of reference."""
        text = extraction.extraction_text
        
        if text in self.PERSON_PRONOUNS or text in self.ORGANIZATION_PRONOUNS:
            return ReferenceType.PRONOUN
        elif text.isupper() and text.isalpha():
            return ReferenceType.ABBREVIATION
        elif ' ' not in text and extraction.extraction_class == 'person':
            return ReferenceType.PARTIAL
        elif text.lower().startswith(('the ', 'this ', 'that ')):
            return ReferenceType.COREFERENCE
        else:
            return ReferenceType.ALIAS
    
    def _find_referent(
        self,
        reference: data.Extraction,
        candidates: List[data.Extraction],
        text: str
    ) -> Optional[data.Extraction]:
        """
        Find what a reference refers to.
        
        Args:
            reference: The reference extraction
            candidates: Previous extractions that could be referents
            text: Original document text
            
        Returns:
            The most likely referent extraction or None
        """
        ref_text = reference.extraction_text
        ref_type = self._get_reference_type(reference)
        
        # Filter compatible candidates
        compatible_candidates = []
        
        for candidate in reversed(candidates):  # Check recent first
            if ref_type == 'pronoun':
                if self._pronoun_compatible(ref_text, candidate):
                    compatible_candidates.append(candidate)
            
            elif ref_type == 'abbreviation':
                if self._abbreviation_matches(ref_text, candidate.extraction_text):
                    compatible_candidates.append(candidate)
            
            elif ref_type == 'partial_name':
                if self._partial_name_matches(ref_text, candidate.extraction_text):
                    compatible_candidates.append(candidate)
            
            elif ref_type == 'definite_reference':
                if self._definite_reference_matches(ref_text, candidate):
                    compatible_candidates.append(candidate)
        
        # Return the closest compatible candidate
        if compatible_candidates:
            return compatible_candidates[0]
        
        return None
    
    def _pronoun_compatible(self, pronoun: str, candidate: data.Extraction) -> bool:
        """Check if a pronoun is compatible with a candidate."""
        if pronoun in self.PERSON_PRONOUNS:
            return candidate.extraction_class in ['person', 'name', 'individual']
        elif pronoun in self.ORGANIZATION_PRONOUNS:
            if pronoun in self.PLURAL_PRONOUNS:
                # Could be multiple people or an organization
                return candidate.extraction_class in ['organization', 'company', 'group', 'people']
            else:
                return candidate.extraction_class in ['organization', 'company', 'entity', 'thing']
        return False
    
    def _abbreviation_matches(self, abbrev: str, full_text: str) -> bool:
        """Check if an abbreviation matches a full text."""
        # Check if abbreviation matches capital letters
        words = full_text.split()
        capitals = ''.join(word[0].upper() for word in words if word)
        
        if capitals == abbrev.upper():
            return True
        
        # Check for common abbreviation patterns
        # e.g., "USA" for "United States of America"
        important_words = [w for w in words if len(w) > 2 and w[0].isupper()]
        important_capitals = ''.join(w[0] for w in important_words)
        
        if important_capitals == abbrev.upper():
            return True
        
        return False
    
    def _partial_name_matches(self, partial: str, full: str) -> bool:
        """Check if a partial name matches a full name."""
        # Check if partial is a word in full
        full_words = full.split()
        partial_lower = partial.lower()
        
        for word in full_words:
            if word.lower() == partial_lower:
                return True
            
            # Check for fuzzy match
            ratio = difflib.SequenceMatcher(None, word.lower(), partial_lower).ratio()
            if ratio >= self.fuzzy_threshold:
                return True
        
        return False
    
    def _definite_reference_matches(self, ref_text: str, candidate: data.Extraction) -> bool:
        """Check if a definite reference matches a candidate."""
        # Remove the definite article
        core_text = ref_text.lower()
        for article in ['the ', 'this ', 'that ', 'these ', 'those ']:
            if core_text.startswith(article):
                core_text = core_text[len(article):]
                break
        
        # Check if core text matches candidate class or text
        candidate_text_lower = candidate.extraction_text.lower()
        
        # Direct match
        if core_text in candidate_text_lower:
            return True
        
        # Class match
        if candidate.extraction_class and core_text in candidate.extraction_class.lower():
            return True
        
        return False
    
    def _calculate_distance(self, extraction1: data.Extraction, extraction2: data.Extraction) -> int:
        """Calculate character distance between two extractions."""
        if (extraction1.char_interval and extraction2.char_interval and
            hasattr(extraction1.char_interval, 'start') and hasattr(extraction2.char_interval, 'start')):
            return abs(extraction1.char_interval.start - extraction2.char_interval.start)
        return 0
    
    def _calculate_confidence(self, reference: data.Extraction, referent: data.Extraction) -> float:
        """Calculate confidence score for a reference resolution."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on proximity
        distance = self._calculate_distance(reference, referent)
        
        if distance < 100:
            confidence += 0.3
        elif distance < 500:
            confidence += 0.2
        elif distance < 1000:
            confidence += 0.1
        
        # Increase confidence for exact type matches
        ref_type = self._get_reference_type(reference)
        if ref_type == ReferenceType.ABBREVIATION:
            confidence += 0.2
        elif ref_type == ReferenceType.PARTIAL:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _add_reference_info(self, extraction: data.Extraction, referent: data.Extraction):
        """Add reference information to an extraction."""
        if extraction.attributes is None:
            extraction.attributes = {}
        
        extraction.attributes['refers_to'] = referent.extraction_text
        extraction.attributes['referent_id'] = referent.extraction_id
        extraction.attributes['referent_class'] = referent.extraction_class
    
    def get_resolved_references(self) -> List[Reference]:
        """Get all resolved references."""
        return self.resolved_references


class RelationshipResolver:
    """
    Identifies and resolves relationships between extracted entities.
    """
    
    def __init__(self, proximity_threshold: int = 100):
        """
        Initialize the relationship resolver.
        
        Args:
            proximity_threshold: Maximum character distance for relationship detection
        """
        self.proximity_threshold = proximity_threshold
        self.relationships: List[Relationship] = []
    
    def resolve_relationships(
        self,
        extractions: List[data.Extraction],
        text: Optional[str] = None
    ) -> List[Relationship]:
        """
        Find relationships between extracted entities.
        
        Args:
            extractions: List of extractions to analyze
            text: Optional original text for context
            
        Returns:
            List of discovered relationships
        """
        self.relationships = []
        
        # Check each pair of extractions
        for i, ext1 in enumerate(extractions):
            for j, ext2 in enumerate(extractions[i+1:], i+1):
                # Look for various relationship types
                relationships = self._find_relationships(ext1, ext2, text)
                self.relationships.extend(relationships)
        
        return self.relationships
    
    def _find_relationships(
        self,
        ext1: data.Extraction,
        ext2: data.Extraction,
        text: Optional[str]
    ) -> List[Relationship]:
        """Find relationships between two extractions."""
        relationships = []
        
        # Check for explicit attribute relationships
        rel = self._check_attribute_relationship(ext1, ext2)
        if rel:
            relationships.append(rel)
        
        # Check for proximity-based relationships
        rel = self._check_proximity_relationship(ext1, ext2)
        if rel:
            relationships.append(rel)
        
        # Check for pattern-based relationships
        if text:
            rel = self._check_pattern_relationship(ext1, ext2, text)
            if rel:
                relationships.append(rel)
        
        return relationships
    
    def _check_attribute_relationship(
        self,
        ext1: data.Extraction,
        ext2: data.Extraction
    ) -> Optional[Relationship]:
        """Check for relationships defined in attributes."""
        # Check if ext1 references ext2
        if ext1.attributes:
            if ext1.attributes.get('parent_id') == ext2.extraction_id:
                return Relationship(
                    entity1_id=ext1.extraction_id or '',
                    entity2_id=ext2.extraction_id or '',
                    relationship_type='child_of',
                    confidence=1.0,
                    evidence='explicit_attribute'
                )
            
            if ext1.attributes.get('refers_to') == ext2.extraction_text:
                return Relationship(
                    entity1_id=ext1.extraction_id or '',
                    entity2_id=ext2.extraction_id or '',
                    relationship_type='references',
                    confidence=0.9,
                    evidence='reference_resolution'
                )
        
        return None
    
    def _check_proximity_relationship(
        self,
        ext1: data.Extraction,
        ext2: data.Extraction
    ) -> Optional[Relationship]:
        """Check for relationships based on proximity."""
        if not (ext1.char_interval and ext2.char_interval):
            return None
        
        if (ext1.char_interval.start_pos is None or 
            ext2.char_interval.start_pos is None):
            return None
        
        distance = abs(ext1.char_interval.start_pos - ext2.char_interval.start_pos)
        
        # Very close entities might be related
        if distance < 50:
            # Check for specific patterns
            if (ext1.extraction_class == 'person' and 
                ext2.extraction_class == 'organization'):
                return Relationship(
                    entity1_id=ext1.extraction_id or '',
                    entity2_id=ext2.extraction_id or '',
                    relationship_type='affiliated_with',
                    confidence=0.7,
                    evidence=f'proximity_{distance}_chars'
                )
            
            if (ext1.extraction_class == 'person' and
                ext2.extraction_class == 'title'):
                return Relationship(
                    entity1_id=ext1.extraction_id or '',
                    entity2_id=ext2.extraction_id or '',
                    relationship_type='has_title',
                    confidence=0.8,
                    evidence=f'proximity_{distance}_chars'
                )
            
            if (ext1.extraction_class == 'date' and
                ext2.extraction_class in ['event', 'action']):
                return Relationship(
                    entity1_id=ext1.extraction_id or '',
                    entity2_id=ext2.extraction_id or '',
                    relationship_type='date_of',
                    confidence=0.75,
                    evidence=f'proximity_{distance}_chars'
                )
        
        return None
    
    def _check_pattern_relationship(
        self,
        ext1: data.Extraction,
        ext2: data.Extraction,
        text: str
    ) -> Optional[Relationship]:
        """Check for relationships based on text patterns."""
        if not (ext1.char_interval and ext2.char_interval):
            return None
        
        if (ext1.char_interval.start_pos is None or 
            ext2.char_interval.end_pos is None):
            return None
        
        # Get text between entities
        start = min(ext1.char_interval.end_pos, ext2.char_interval.end_pos)
        end = max(ext1.char_interval.start_pos, ext2.char_interval.start_pos)
        
        if start < end and end - start < 100:
            between_text = text[start:end].lower()
            
            # Look for relationship indicators
            if any(word in between_text for word in [' of ', ' from ', ' at ']):
                if ext1.extraction_class == 'person' and ext2.extraction_class == 'organization':
                    return Relationship(
                        entity1_id=ext1.extraction_id or '',
                        entity2_id=ext2.extraction_id or '',
                        relationship_type='member_of',
                        confidence=0.6,
                        evidence='pattern_match'
                    )
            
            if any(word in between_text for word in [' founded ', ' created ', ' established ']):
                return Relationship(
                    entity1_id=ext1.extraction_id or '',
                    entity2_id=ext2.extraction_id or '',
                    relationship_type='founded',
                    confidence=0.8,
                    evidence='pattern_match'
                )
        
        return None


__all__ = [
    'ReferenceResolver',
    'RelationshipResolver',
    'Reference',
    'Relationship',
]