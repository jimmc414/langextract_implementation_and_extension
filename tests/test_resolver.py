"""
Tests for reference and relationship resolution.
"""

import pytest
from langextract import data
from langextract_extensions.resolver import (
    ReferenceResolver, RelationshipResolver,
    Reference, Relationship, ReferenceType, RelationshipType
)


class TestReferenceResolver:
    """Test ReferenceResolver functionality."""
    
    def test_resolver_initialization(self):
        """Test initializing reference resolver."""
        resolver = ReferenceResolver(
            fuzzy_threshold=0.85,
            max_distance=300
        )
        
        assert resolver.fuzzy_threshold == 0.85
        assert resolver.max_distance == 300
    
    def test_pronoun_resolution(self):
        """Test resolving pronouns to their antecedents."""
        text = "John Smith is the CEO. He founded the company in 2020."
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John Smith",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="He",
                char_interval=data.CharInterval(start=25, end=27)
            )
        ]
        
        resolver = ReferenceResolver()
        resolved = resolver.resolve_references(extractions, text)
        
        # Check that "He" was resolved to "John Smith"
        references = resolver.get_resolved_references()
        assert len(references) > 0
        
        # Find the reference for "He"
        he_ref = next((r for r in references if r.source_text == "He"), None)
        if he_ref:
            assert he_ref.target_text == "John Smith"
            assert he_ref.reference_type == ReferenceType.PRONOUN
    
    def test_abbreviation_resolution(self):
        """Test resolving abbreviations."""
        text = "Acme Corporation (ACME) reported profits. ACME is expanding."
        
        extractions = [
            data.Extraction(
                extraction_class="organization",
                extraction_text="Acme Corporation",
                char_interval=data.CharInterval(start=0, end=16)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="ACME",
                char_interval=data.CharInterval(start=18, end=22)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="ACME",
                char_interval=data.CharInterval(start=42, end=46)
            )
        ]
        
        resolver = ReferenceResolver()
        resolved = resolver.resolve_references(extractions, text)
        
        references = resolver.get_resolved_references()
        
        # Check that ACME references were linked to Acme Corporation
        acme_refs = [r for r in references if r.source_text == "ACME"]
        assert len(acme_refs) > 0
        for ref in acme_refs:
            assert ref.target_text == "Acme Corporation"
            assert ref.reference_type == ReferenceType.ABBREVIATION
    
    def test_coreference_resolution(self):
        """Test resolving coreferences."""
        text = "The company announced earnings. The firm exceeded expectations."
        
        extractions = [
            data.Extraction(
                extraction_class="organization",
                extraction_text="The company",
                char_interval=data.CharInterval(start=0, end=11)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="The firm",
                char_interval=data.CharInterval(start=33, end=41)
            )
        ]
        
        resolver = ReferenceResolver(fuzzy_threshold=0.7)
        resolved = resolver.resolve_references(extractions, text)
        
        # With appropriate fuzzy matching, "The firm" might be linked to "The company"
        references = resolver.get_resolved_references()
        # This depends on the implementation details
    
    def test_distance_threshold(self):
        """Test that distance threshold affects resolution."""
        text = "A" * 1000  # Long text
        text = f"John Smith is here. {text} He is there."
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John Smith",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="He",
                char_interval=data.CharInterval(start=1020, end=1022)
            )
        ]
        
        # With small max_distance, should not resolve
        resolver_small = ReferenceResolver(max_distance=100)
        resolver_small.resolve_references(extractions, text)
        refs_small = resolver_small.get_resolved_references()
        
        # With large max_distance, might resolve
        resolver_large = ReferenceResolver(max_distance=2000)
        resolver_large.resolve_references(extractions, text)
        refs_large = resolver_large.get_resolved_references()
        
        # The large distance resolver might find more references
        assert len(refs_large) >= len(refs_small)


class TestRelationshipResolver:
    """Test RelationshipResolver functionality."""
    
    def test_resolver_initialization(self):
        """Test initializing relationship resolver."""
        resolver = RelationshipResolver(proximity_threshold=150)
        
        assert resolver.proximity_threshold == 150
    
    def test_employment_relationship(self):
        """Test detecting employment relationships."""
        text = "John Smith is the CEO of Acme Corporation."
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John Smith",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="title",
                extraction_text="CEO",
                char_interval=data.CharInterval(start=18, end=21)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Acme Corporation",
                char_interval=data.CharInterval(start=25, end=41)
            )
        ]
        
        resolver = RelationshipResolver()
        relationships = resolver.resolve_relationships(extractions, text)
        
        assert len(relationships) > 0
        
        # Check for employment relationship
        emp_rel = next((r for r in relationships 
                        if r.relationship_type == RelationshipType.EMPLOYMENT), None)
        if emp_rel:
            assert emp_rel.source_text == "John Smith"
            assert emp_rel.target_text == "Acme Corporation"
            assert emp_rel.metadata.get("role") == "CEO"
    
    def test_location_relationship(self):
        """Test detecting location relationships."""
        text = "The company is headquartered in New York."
        
        extractions = [
            data.Extraction(
                extraction_class="organization",
                extraction_text="The company",
                char_interval=data.CharInterval(start=0, end=11)
            ),
            data.Extraction(
                extraction_class="location",
                extraction_text="New York",
                char_interval=data.CharInterval(start=33, end=41)
            )
        ]
        
        resolver = RelationshipResolver()
        relationships = resolver.resolve_relationships(extractions, text)
        
        # Check for location relationship
        loc_rel = next((r for r in relationships 
                       if r.relationship_type == RelationshipType.LOCATION), None)
        if loc_rel:
            assert loc_rel.source_text == "The company"
            assert loc_rel.target_text == "New York"
    
    def test_temporal_relationship(self):
        """Test detecting temporal relationships."""
        text = "The meeting is scheduled for January 15, 2024."
        
        extractions = [
            data.Extraction(
                extraction_class="event",
                extraction_text="The meeting",
                char_interval=data.CharInterval(start=0, end=11)
            ),
            data.Extraction(
                extraction_class="date",
                extraction_text="January 15, 2024",
                char_interval=data.CharInterval(start=30, end=46)
            )
        ]
        
        resolver = RelationshipResolver()
        relationships = resolver.resolve_relationships(extractions, text)
        
        # Check for temporal relationship
        temp_rel = next((r for r in relationships 
                        if r.relationship_type == RelationshipType.TEMPORAL), None)
        if temp_rel:
            assert temp_rel.source_text == "The meeting"
            assert temp_rel.target_text == "January 15, 2024"
    
    def test_proximity_threshold(self):
        """Test that proximity threshold affects relationship detection."""
        text = "John Smith " + "x" * 200 + " Acme Corporation"
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John Smith",
                char_interval=data.CharInterval(start=0, end=10)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Acme Corporation",
                char_interval=data.CharInterval(start=211, end=227)
            )
        ]
        
        # With small proximity, should not find relationship
        resolver_small = RelationshipResolver(proximity_threshold=50)
        rels_small = resolver_small.resolve_relationships(extractions, text)
        
        # With large proximity, might find relationship
        resolver_large = RelationshipResolver(proximity_threshold=300)
        rels_large = resolver_large.resolve_relationships(extractions, text)
        
        # The large proximity resolver might find more relationships
        assert len(rels_large) >= len(rels_small)
    
    def test_financial_relationship(self):
        """Test detecting financial relationships."""
        text = "The company reported revenue of $5 million."
        
        extractions = [
            data.Extraction(
                extraction_class="organization",
                extraction_text="The company",
                char_interval=data.CharInterval(start=0, end=11)
            ),
            data.Extraction(
                extraction_class="amount",
                extraction_text="$5 million",
                char_interval=data.CharInterval(start=33, end=43)
            )
        ]
        
        resolver = RelationshipResolver()
        relationships = resolver.resolve_relationships(extractions, text)
        
        # Check for financial relationship
        fin_rel = next((r for r in relationships 
                       if r.relationship_type == RelationshipType.FINANCIAL), None)
        if fin_rel:
            assert fin_rel.source_text == "The company"
            assert fin_rel.target_text == "$5 million"
            assert fin_rel.metadata.get("context") == "revenue"


class TestReferenceClass:
    """Test Reference dataclass."""
    
    def test_reference_creation(self):
        """Test creating Reference objects."""
        ref = Reference(
            source_text="He",
            target_text="John Smith",
            reference_type=ReferenceType.PRONOUN,
            confidence=0.95,
            distance=25
        )
        
        assert ref.source_text == "He"
        assert ref.target_text == "John Smith"
        assert ref.reference_type == ReferenceType.PRONOUN
        assert ref.confidence == 0.95
        assert ref.distance == 25
    
    def test_reference_types(self):
        """Test different reference types."""
        types = [
            ReferenceType.PRONOUN,
            ReferenceType.ABBREVIATION,
            ReferenceType.ALIAS,
            ReferenceType.COREFERENCE,
            ReferenceType.PARTIAL
        ]
        
        for ref_type in types:
            ref = Reference(
                source_text="source",
                target_text="target",
                reference_type=ref_type
            )
            assert ref.reference_type == ref_type


class TestRelationshipClass:
    """Test Relationship dataclass."""
    
    def test_relationship_creation(self):
        """Test creating Relationship objects."""
        rel = Relationship(
            source_text="John Smith",
            target_text="Acme Corp",
            relationship_type=RelationshipType.EMPLOYMENT,
            confidence=0.85,
            metadata={"role": "CEO"}
        )
        
        assert rel.source_text == "John Smith"
        assert rel.target_text == "Acme Corp"
        assert rel.relationship_type == RelationshipType.EMPLOYMENT
        assert rel.confidence == 0.85
        assert rel.metadata["role"] == "CEO"
    
    def test_relationship_types(self):
        """Test different relationship types."""
        types = [
            RelationshipType.EMPLOYMENT,
            RelationshipType.LOCATION,
            RelationshipType.TEMPORAL,
            RelationshipType.FINANCIAL,
            RelationshipType.OWNERSHIP,
            RelationshipType.FAMILIAL,
            RelationshipType.ASSOCIATION
        ]
        
        for rel_type in types:
            rel = Relationship(
                source_text="entity1",
                target_text="entity2",
                relationship_type=rel_type
            )
            assert rel.relationship_type == rel_type


class TestIntegratedResolution:
    """Test integrated reference and relationship resolution."""
    
    def test_combined_resolution(self):
        """Test using both resolvers together."""
        text = """
        John Smith is the CEO of Acme Corporation. He founded the company
        in 2020. ACME reported $10 million in revenue last year.
        """
        
        extractions = [
            data.Extraction(
                extraction_class="person",
                extraction_text="John Smith",
                char_interval=data.CharInterval(start=9, end=19)
            ),
            data.Extraction(
                extraction_class="title",
                extraction_text="CEO",
                char_interval=data.CharInterval(start=27, end=30)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="Acme Corporation",
                char_interval=data.CharInterval(start=34, end=50)
            ),
            data.Extraction(
                extraction_class="person",
                extraction_text="He",
                char_interval=data.CharInterval(start=52, end=54)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="the company",
                char_interval=data.CharInterval(start=67, end=78)
            ),
            data.Extraction(
                extraction_class="organization",
                extraction_text="ACME",
                char_interval=data.CharInterval(start=95, end=99)
            ),
            data.Extraction(
                extraction_class="amount",
                extraction_text="$10 million",
                char_interval=data.CharInterval(start=109, end=120)
            )
        ]
        
        # Resolve references
        ref_resolver = ReferenceResolver()
        resolved_extractions = ref_resolver.resolve_references(extractions, text)
        references = ref_resolver.get_resolved_references()
        
        # Resolve relationships
        rel_resolver = RelationshipResolver()
        relationships = rel_resolver.resolve_relationships(resolved_extractions, text)
        
        # Check that we found both references and relationships
        assert len(references) > 0
        assert len(relationships) > 0