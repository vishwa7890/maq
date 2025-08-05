"""
Knowledge Graph module for storing and querying business knowledge.
"""
from typing import Dict, List, Optional
import networkx as nx
from dataclasses import dataclass

@dataclass
class Entity:
    id: str
    type: str  # e.g., 'product', 'service', 'client', 'requirement'
    name: str
    attributes: Dict[str, any]

class BusinessKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()
        
    def add_entity(self, entity: Entity):
        """Add or update an entity in the knowledge graph."""
        self.graph.add_node(entity.id, 
                          type=entity.type,
                          name=entity.name,
                          **entity.attributes)
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str):
        """Add a relationship between two entities."""
        if source_id in self.graph and target_id in self.graph:
            self.graph.add_edge(source_id, target_id, type=relation_type)
    
    def find_related_entities(self, entity_id: str, relation_type: Optional[str] = None):
        """Find entities related to the given entity, optionally filtered by relation type."""
        if entity_id not in self.graph:
            return []
            
        related = []
        for neighbor in self.graph.neighbors(entity_id):
            edge_data = self.graph.get_edge_data(entity_id, neighbor)
            if relation_type is None or edge_data.get('type') == relation_type:
                related.append((neighbor, edge_data.get('type')))
        return related
    
    def search_entities(self, query: str, entity_type: Optional[str] = None):
        """Search for entities by name and optionally filter by type."""
        results = []
        for node_id, data in self.graph.nodes(data=True):
            if query.lower() in data.get('name', '').lower() and \
               (entity_type is None or data.get('type') == entity_type):
                results.append((node_id, data))
        return results
    
    def get_context_for_query(self, query: str) -> str:
        """Generate context from the knowledge graph relevant to the query."""
        # Simple implementation - can be enhanced with NLP for better matching
        context = []
        
        # Search for direct matches
        for entity_id, data in self.search_entities(query):
            context.append(f"{data['type'].title()}: {data['name']}")
            context.extend(f"  - {attr}: {val}" for attr, val in data.items() 
                         if attr not in ['type', 'name'])
            
            # Add related entities
            for related_id, rel_type in self.find_related_entities(entity_id):
                related_data = self.graph.nodes[related_id]
                context.append(f"  - {rel_type}: {related_data['name']} ({related_data['type']})")
        
        return "\n".join(context) if context else "No relevant information found in knowledge base."

    def get_business_context(self, query: str) -> str:
        """
        Generate business context for a query by searching entities and relationships.
        Returns formatted string with relevant business information.
        """
        context_lines = []
        
        # Find matching entities
        matches = self.search_entities(query)
        
        for entity_id, entity_data in matches:
            # Add entity info
            context_lines.append(f"{entity_data['type'].title()}: {entity_data['name']}")
            
            # Add attributes
            for attr, value in entity_data.items():
                if attr not in ['type', 'name']:
                    context_lines.append(f"  - {attr}: {value}")
            
            # Add relationships
            related = self.find_related_entities(entity_id)
            if related:
                context_lines.append("  Related:")
                for related_id, rel_type in related:
                    related_data = self.graph.nodes[related_id]
                    context_lines.append(f"    - {rel_type}: {related_data['name']} ({related_data['type']})")
        
        return "\n".join(context_lines) if context_lines else "No relevant business context found"
