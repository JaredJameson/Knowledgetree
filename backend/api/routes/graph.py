"""
KnowledgeTree - Graph API Routes
API endpoints for Knowledge Graph visualization and analysis

Phase 3: Knowledge Graph Visualization

Endpoints:
- POST /api/v1/graph/projects/{project_id}/build - Build knowledge graph
- GET /api/v1/graph/projects/{project_id}/entities - List entities
- GET /api/v1/graph/projects/{project_id}/relationships - List relationships
- GET /api/v1/graph/entities/{entity_id} - Get entity details with neighbors
- POST /api/v1/graph/path - Find shortest path between entities
- GET /api/v1/graph/projects/{project_id}/clusters - Get communities/clusters
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import community as community_louvain

from core.database import get_db
from api.dependencies.auth import get_current_user
from models.user import User
from models.project import Project
from models.entity import Entity, EntityRelationship
from services.graph_builder import GraphBuilder
from schemas.graph import (
    BuildGraphRequest,
    KnowledgeGraphResponse,
    EntityListResponse,
    EntityListItem,
    RelationshipListResponse,
    RelationshipListItem,
    EntityDetailsResponse,
    EntityNeighbor,
    PathResponse,
    PathNode,
    CommunitiesResponse,
    Community,
    FindPathRequest,
    GraphNode,
    GraphEdge,
    GraphStatistics,
    CentralityMetrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


async def verify_project_access(
    project_id: int,
    current_user: User,
    db: AsyncSession
) -> Project:
    """
    Verify user has access to project.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Returns:
        Project object

    Raises:
        HTTPException: If project not found or access denied
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return project


@router.post("/projects/{project_id}/build", response_model=KnowledgeGraphResponse)
async def build_knowledge_graph(
    project_id: int,
    request: BuildGraphRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Build knowledge graph for a project.

    Creates NetworkX graph from entities and relationships, runs community
    detection, calculates centrality metrics, and returns complete graph data.

    **Parameters:**
    - **project_id**: Project ID
    - **min_strength**: Minimum relationship strength to include (0.0-1.0)
    - **include_isolated**: Include entities with no relationships
    - **include_communities**: Run community detection
    - **include_centrality**: Calculate centrality metrics
    - **include_clustering**: Calculate clustering coefficients

    **Returns:**
    Complete knowledge graph with nodes, edges, and statistics
    """
    logger.info(f"Building graph for project {project_id}")

    # Verify access
    await verify_project_access(project_id, current_user, db)

    # Build graph
    graph_builder = GraphBuilder(db)

    try:
        await graph_builder.build_graph(
            project_id=project_id,
            min_strength=request.min_strength,
            include_isolated=request.include_isolated
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Export to dict
    graph_dict = graph_builder.export_to_dict(
        include_communities=request.include_communities,
        include_centrality=request.include_centrality,
        include_clustering=request.include_clustering
    )

    # Convert to response schema
    return KnowledgeGraphResponse(**graph_dict)


@router.get("/projects/{project_id}/entities", response_model=EntityListResponse)
async def list_project_entities(
    project_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    entity_type: str = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List entities for a project.

    **Parameters:**
    - **project_id**: Project ID
    - **limit**: Maximum number of entities to return (1-1000)
    - **offset**: Number of entities to skip
    - **entity_type**: Filter by entity type (person/organization/location/concept/event)

    **Returns:**
    List of entities with basic information
    """
    logger.info(f"Listing entities for project {project_id}")

    # Verify access
    await verify_project_access(project_id, current_user, db)

    # Build query
    query = select(Entity).where(Entity.project_id == project_id)

    if entity_type:
        query = query.where(Entity.entity_type == entity_type)

    query = query.order_by(Entity.occurrence_count.desc())
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    entities = result.scalars().all()

    # Get total count
    count_query = select(Entity).where(Entity.project_id == project_id)
    if entity_type:
        count_query = count_query.where(Entity.entity_type == entity_type)

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # Convert to response
    return EntityListResponse(
        total=total,
        entities=[
            EntityListItem(
                id=e.id,
                name=e.name,
                type=e.entity_type,
                occurrence_count=e.occurrence_count
            )
            for e in entities
        ]
    )


@router.get("/projects/{project_id}/relationships", response_model=RelationshipListResponse)
async def list_project_relationships(
    project_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    min_strength: float = Query(default=0.0, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List relationships for a project.

    **Parameters:**
    - **project_id**: Project ID
    - **limit**: Maximum number of relationships to return (1-1000)
    - **offset**: Number of relationships to skip
    - **min_strength**: Minimum relationship strength (0.0-1.0)

    **Returns:**
    List of relationships with source/target entity names
    """
    logger.info(f"Listing relationships for project {project_id}")

    # Verify access
    await verify_project_access(project_id, current_user, db)

    # Build query
    query = (
        select(EntityRelationship)
        .where(
            EntityRelationship.project_id == project_id,
            EntityRelationship.strength >= min_strength
        )
        .order_by(EntityRelationship.strength.desc())
        .offset(offset)
        .limit(limit)
    )

    # Execute query
    result = await db.execute(query)
    relationships = result.scalars().all()

    # Get entity names
    relationship_list = []
    for rel in relationships:
        # Get source entity
        source_result = await db.execute(
            select(Entity).where(Entity.id == rel.source_entity_id)
        )
        source = source_result.scalar_one()

        # Get target entity
        target_result = await db.execute(
            select(Entity).where(Entity.id == rel.target_entity_id)
        )
        target = target_result.scalar_one()

        relationship_list.append(
            RelationshipListItem(
                id=rel.id,
                source_id=rel.source_entity_id,
                source_name=source.name,
                target_id=rel.target_entity_id,
                target_name=target.name,
                strength=rel.strength,
                co_occurrence_count=rel.co_occurrence_count
            )
        )

    # Get total count
    count_query = select(EntityRelationship).where(
        EntityRelationship.project_id == project_id,
        EntityRelationship.strength >= min_strength
    )
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return RelationshipListResponse(
        total=total,
        relationships=relationship_list
    )


@router.get("/entities/{entity_id}", response_model=EntityDetailsResponse)
async def get_entity_details(
    entity_id: int,
    depth: int = Query(default=1, ge=1, le=3),
    min_weight: float = Query(default=0.0, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get entity details with neighbors.

    **Parameters:**
    - **entity_id**: Entity ID
    - **depth**: Neighbor depth (1-3 hops)
    - **min_weight**: Minimum edge weight for neighbors

    **Returns:**
    Entity details with neighboring entities
    """
    logger.info(f"Getting details for entity {entity_id}")

    # Get entity
    result = await db.execute(
        select(Entity).where(Entity.id == entity_id)
    )
    entity = result.scalar_one_or_none()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Verify project access
    await verify_project_access(entity.project_id, current_user, db)

    # Build graph
    graph_builder = GraphBuilder(db)
    await graph_builder.build_graph(entity.project_id)

    # Get neighbors
    neighbors = graph_builder.get_entity_neighbors(
        entity_id=entity_id,
        depth=depth,
        min_weight=min_weight
    )

    # Get centrality and clustering if node is in graph
    centrality = None
    clustering = None

    if graph_builder.graph and entity_id in graph_builder.graph.nodes:
        centrality_metrics = graph_builder.calculate_centrality_metrics()
        clustering_coeff = graph_builder.calculate_clustering_coefficient()

        centrality = CentralityMetrics(
            degree=centrality_metrics['degree'].get(entity_id, 0.0),
            betweenness=centrality_metrics['betweenness'].get(entity_id, 0.0),
            closeness=centrality_metrics['closeness'].get(entity_id, 0.0),
            eigenvector=centrality_metrics['eigenvector'].get(entity_id, 0.0)
        )
        clustering = clustering_coeff.get(entity_id, 0.0)

        # Get community
        communities = graph_builder.detect_communities()
        community_id = communities.get(entity_id)
    else:
        community_id = None

    return EntityDetailsResponse(
        id=entity.id,
        name=entity.name,
        type=entity.entity_type,
        occurrence_count=entity.occurrence_count,
        community=community_id,
        centrality=centrality,
        clustering=clustering,
        neighbors=[EntityNeighbor(**n) for n in neighbors]
    )


@router.post("/path", response_model=PathResponse)
async def find_shortest_path(
    request: FindPathRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Find shortest path between two entities.

    Uses Dijkstra's algorithm to find the shortest path. If weighted=True,
    uses relationship strength as edge weights (stronger = shorter distance).

    **Parameters:**
    - **source_entity_id**: Source entity ID
    - **target_entity_id**: Target entity ID
    - **weighted**: Use edge weights (relationship strength)

    **Returns:**
    Shortest path or indication that no path exists
    """
    logger.info(f"Finding path from {request.source_entity_id} to {request.target_entity_id}")

    # Get source entity to determine project
    result = await db.execute(
        select(Entity).where(Entity.id == request.source_entity_id)
    )
    source_entity = result.scalar_one_or_none()

    if not source_entity:
        raise HTTPException(status_code=404, detail="Source entity not found")

    # Verify project access
    await verify_project_access(source_entity.project_id, current_user, db)

    # Verify target entity exists in same project
    result = await db.execute(
        select(Entity).where(Entity.id == request.target_entity_id)
    )
    target_entity = result.scalar_one_or_none()

    if not target_entity:
        raise HTTPException(status_code=404, detail="Target entity not found")

    if target_entity.project_id != source_entity.project_id:
        raise HTTPException(
            status_code=400,
            detail="Source and target entities must be in the same project"
        )

    # Build graph
    graph_builder = GraphBuilder(db)
    await graph_builder.build_graph(source_entity.project_id)

    # Find path
    path = graph_builder.find_shortest_path(
        source_entity_id=request.source_entity_id,
        target_entity_id=request.target_entity_id,
        weight='weight' if request.weighted else None
    )

    if path is None:
        return PathResponse(exists=False, length=None, path=None, total_weight=None)

    # Convert to response
    path_nodes = [
        PathNode(
            id=node_id,
            name=graph_builder.entity_id_to_name[node_id]
        )
        for node_id in path
    ]

    # Calculate total weight
    total_weight = 0.0
    for i in range(len(path) - 1):
        edge_data = graph_builder.graph[path[i]][path[i+1]]
        total_weight += edge_data['weight']

    return PathResponse(
        exists=True,
        length=len(path) - 1,  # Number of edges
        path=path_nodes,
        total_weight=total_weight
    )


@router.get("/projects/{project_id}/clusters", response_model=CommunitiesResponse)
async def get_project_clusters(
    project_id: int,
    resolution: float = Query(default=1.0, ge=0.1, le=10.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get communities/clusters for a project.

    Uses Louvain algorithm for community detection. Higher resolution
    values produce more, smaller communities.

    **Parameters:**
    - **project_id**: Project ID
    - **resolution**: Resolution parameter (0.1-10.0, default 1.0)

    **Returns:**
    List of communities with member entities
    """
    logger.info(f"Detecting communities for project {project_id}")

    # Verify access
    await verify_project_access(project_id, current_user, db)

    # Build graph
    graph_builder = GraphBuilder(db)

    try:
        await graph_builder.build_graph(project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Detect communities
    communities_dict = graph_builder.detect_communities(resolution=resolution)

    # Group entities by community
    community_groups = {}
    for entity_id, comm_id in communities_dict.items():
        if comm_id not in community_groups:
            community_groups[comm_id] = []
        community_groups[comm_id].append(entity_id)

    # Convert to response
    communities = [
        Community(
            id=comm_id,
            size=len(members),
            entities=members
        )
        for comm_id, members in sorted(community_groups.items())
    ]

    # Calculate modularity
    modularity = community_louvain.modularity(
        communities_dict,
        graph_builder.graph,
        weight='weight'
    )

    return CommunitiesResponse(
        num_communities=len(communities),
        communities=communities,
        modularity=modularity
    )
