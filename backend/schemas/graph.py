"""
KnowledgeTree - Graph Schemas
Pydantic schemas for Knowledge Graph API endpoints
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class BuildGraphRequest(BaseModel):
    """Request for building knowledge graph"""
    min_strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum relationship strength to include (0.0-1.0)"
    )
    include_isolated: bool = Field(
        default=False,
        description="Include entities with no relationships"
    )
    include_communities: bool = Field(
        default=True,
        description="Run community detection"
    )
    include_centrality: bool = Field(
        default=True,
        description="Calculate centrality metrics"
    )
    include_clustering: bool = Field(
        default=True,
        description="Calculate clustering coefficients"
    )


class FindPathRequest(BaseModel):
    """Request for finding shortest path between entities"""
    source_entity_id: int = Field(..., description="Source entity ID")
    target_entity_id: int = Field(..., description="Target entity ID")
    weighted: bool = Field(
        default=True,
        description="Use edge weights (strength) for path calculation"
    )


# ============================================================================
# Response Schemas
# ============================================================================

class CentralityMetrics(BaseModel):
    """Centrality metrics for an entity"""
    degree: float = Field(..., description="Degree centrality (0.0-1.0)")
    betweenness: float = Field(..., description="Betweenness centrality (0.0-1.0)")
    closeness: float = Field(..., description="Closeness centrality (0.0-1.0)")
    eigenvector: float = Field(..., description="Eigenvector centrality (0.0-1.0)")


class GraphNode(BaseModel):
    """Node in knowledge graph"""
    id: int = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (person/organization/location/concept/event)")
    occurrence_count: int = Field(..., description="Number of times entity appears in documents")
    community: Optional[int] = Field(None, description="Community/cluster ID")
    centrality: Optional[CentralityMetrics] = Field(None, description="Centrality metrics")
    clustering: Optional[float] = Field(None, description="Clustering coefficient (0.0-1.0)")


class GraphEdge(BaseModel):
    """Edge in knowledge graph"""
    source: int = Field(..., description="Source entity ID")
    target: int = Field(..., description="Target entity ID")
    weight: float = Field(..., description="Relationship strength (0.0-1.0)")
    co_occurrence_count: int = Field(..., description="Number of co-occurrences")


class GraphStatistics(BaseModel):
    """Graph statistics"""
    nodes: int = Field(..., description="Number of nodes")
    edges: int = Field(..., description="Number of edges")
    density: float = Field(..., description="Graph density (0.0-1.0)")
    components: int = Field(..., description="Number of connected components")
    avg_degree: float = Field(..., description="Average node degree")
    avg_clustering: float = Field(..., description="Average clustering coefficient")
    diameter: Optional[int] = Field(None, description="Graph diameter (longest shortest path)")
    radius: Optional[int] = Field(None, description="Graph radius (minimum eccentricity)")
    largest_component_size: Optional[int] = Field(
        None,
        description="Size of largest connected component (for disconnected graphs)"
    )


class KnowledgeGraphResponse(BaseModel):
    """Complete knowledge graph response"""
    nodes: List[GraphNode] = Field(..., description="Graph nodes (entities)")
    edges: List[GraphEdge] = Field(..., description="Graph edges (relationships)")
    statistics: GraphStatistics = Field(..., description="Graph statistics")


class EntityNeighbor(BaseModel):
    """Neighbor entity"""
    id: int = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    distance: int = Field(..., description="Distance from source entity (number of hops)")
    path_weight: float = Field(..., description="Edge weight to neighbor")


class EntityDetailsResponse(BaseModel):
    """Entity details with neighbors"""
    id: int = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type")
    occurrence_count: int = Field(..., description="Number of occurrences")
    community: Optional[int] = Field(None, description="Community ID")
    centrality: Optional[CentralityMetrics] = Field(None, description="Centrality metrics")
    clustering: Optional[float] = Field(None, description="Clustering coefficient")
    neighbors: List[EntityNeighbor] = Field(..., description="Neighboring entities")


class PathNode(BaseModel):
    """Node in path"""
    id: int = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")


class PathResponse(BaseModel):
    """Shortest path response"""
    exists: bool = Field(..., description="Whether path exists")
    length: Optional[int] = Field(None, description="Path length (number of edges)")
    path: Optional[List[PathNode]] = Field(None, description="Path nodes from source to target")
    total_weight: Optional[float] = Field(None, description="Total path weight")


class Community(BaseModel):
    """Community/cluster"""
    id: int = Field(..., description="Community ID")
    size: int = Field(..., description="Number of entities in community")
    entities: List[int] = Field(..., description="Entity IDs in community")


class CommunitiesResponse(BaseModel):
    """Communities/clusters response"""
    num_communities: int = Field(..., description="Number of communities detected")
    communities: List[Community] = Field(..., description="Community details")
    modularity: float = Field(..., description="Modularity score (quality metric)")


# ============================================================================
# Entity List Response (for entities endpoint)
# ============================================================================

class EntityListItem(BaseModel):
    """Entity in list"""
    id: int = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type")
    occurrence_count: int = Field(..., description="Number of occurrences")


class EntityListResponse(BaseModel):
    """List of entities"""
    total: int = Field(..., description="Total number of entities")
    entities: List[EntityListItem] = Field(..., description="Entity list")


# ============================================================================
# Relationship List Response
# ============================================================================

class RelationshipListItem(BaseModel):
    """Relationship in list"""
    id: int = Field(..., description="Relationship ID")
    source_id: int = Field(..., description="Source entity ID")
    source_name: str = Field(..., description="Source entity name")
    target_id: int = Field(..., description="Target entity ID")
    target_name: str = Field(..., description="Target entity name")
    strength: float = Field(..., description="Relationship strength (0.0-1.0)")
    co_occurrence_count: int = Field(..., description="Co-occurrence count")


class RelationshipListResponse(BaseModel):
    """List of relationships"""
    total: int = Field(..., description="Total number of relationships")
    relationships: List[RelationshipListItem] = Field(..., description="Relationship list")
