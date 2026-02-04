"""
KnowledgeTree - Graph Builder Service
Phase 3: Knowledge Graph Visualization - Graph Analysis and Community Detection

This service provides:
1. Graph construction from entities and relationships
2. Community detection (Louvain algorithm)
3. Shortest path finding (Dijkstra algorithm)
4. Graph metrics (centrality, clustering coefficient)
5. Graph export to various formats (JSON, GraphML, etc.)

Uses NetworkX for graph analysis and python-louvain for community detection.
"""

import logging
from typing import List, Dict, Set, Optional, Tuple, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import networkx as nx
import community as community_louvain  # python-louvain
from sklearn.preprocessing import MinMaxScaler

from models.entity import Entity, EntityRelationship
from models.project import Project

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Graph Builder Service for Knowledge Graph construction and analysis.

    Uses NetworkX to build an undirected weighted graph from entities
    and relationships, then applies various graph algorithms for analysis.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize graph builder.

        Args:
            db: Database session
        """
        self.db = db
        self.graph: Optional[nx.Graph] = None
        self.entity_id_to_name: Dict[int, str] = {}
        self.entity_name_to_id: Dict[str, int] = {}

    async def build_graph(
        self,
        project_id: int,
        min_strength: float = 0.0,
        include_isolated: bool = False
    ) -> nx.Graph:
        """
        Build NetworkX graph from project entities and relationships.

        Creates an undirected weighted graph where:
        - Nodes: Entities with attributes (type, occurrence_count)
        - Edges: Relationships with weight based on strength

        Args:
            project_id: Project ID to build graph for
            min_strength: Minimum relationship strength to include (0.0-1.0)
            include_isolated: Whether to include isolated nodes (no edges)

        Returns:
            NetworkX Graph object

        Raises:
            ValueError: If project not found or no entities exist
        """
        logger.info(f"Building graph for project {project_id} (min_strength={min_strength})")

        # Verify project exists
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Load entities
        result = await self.db.execute(
            select(Entity).where(Entity.project_id == project_id)
        )
        entities = result.scalars().all()

        if not entities:
            raise ValueError(f"No entities found for project {project_id}")

        logger.info(f"Loaded {len(entities)} entities")

        # Create graph
        G = nx.Graph()

        # Build entity ID mappings
        self.entity_id_to_name = {e.id: e.name for e in entities}
        self.entity_name_to_id = {e.name: e.id for e in entities}

        # Add nodes with attributes
        for entity in entities:
            G.add_node(
                entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                occurrence_count=entity.occurrence_count,
                label=entity.name  # For visualization
            )

        # Load relationships
        result = await self.db.execute(
            select(EntityRelationship)
            .where(
                EntityRelationship.project_id == project_id,
                EntityRelationship.strength >= min_strength
            )
        )
        relationships = result.scalars().all()

        logger.info(f"Loaded {len(relationships)} relationships (filtered by min_strength)")

        # Add edges with weights
        for rel in relationships:
            # Skip if nodes don't exist (shouldn't happen with proper FK constraints)
            if rel.source_entity_id not in G.nodes or rel.target_entity_id not in G.nodes:
                logger.warning(f"Skipping relationship {rel.id} - missing node")
                continue

            G.add_edge(
                rel.source_entity_id,
                rel.target_entity_id,
                weight=rel.strength,
                co_occurrence_count=rel.co_occurrence_count,
                relationship_type=rel.relationship_type
            )

        # Remove isolated nodes if requested
        if not include_isolated:
            isolated = list(nx.isolates(G))
            G.remove_nodes_from(isolated)
            logger.info(f"Removed {len(isolated)} isolated nodes")

        logger.info(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        self.graph = G
        return G

    def detect_communities(
        self,
        resolution: float = 1.0
    ) -> Dict[int, int]:
        """
        Detect communities using Louvain algorithm.

        The Louvain method is a greedy optimization algorithm that finds
        high modularity partitions of large networks.

        Args:
            resolution: Resolution parameter (default 1.0)
                       Higher values = more communities, smaller size
                       Lower values = fewer communities, larger size

        Returns:
            Dictionary mapping entity_id to community_id
            {entity_id: community_id}

        Raises:
            ValueError: If graph not built yet
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        logger.info(f"Detecting communities (resolution={resolution})")

        # Run Louvain community detection
        communities = community_louvain.best_partition(
            self.graph,
            weight='weight',
            resolution=resolution
        )

        # Log community statistics
        num_communities = len(set(communities.values()))
        community_sizes = {}
        for node, comm_id in communities.items():
            community_sizes[comm_id] = community_sizes.get(comm_id, 0) + 1

        logger.info(f"Found {num_communities} communities")
        logger.info(f"Community sizes: {dict(sorted(community_sizes.items()))}")

        return communities

    def find_shortest_path(
        self,
        source_entity_id: int,
        target_entity_id: int,
        weight: Optional[str] = 'weight'
    ) -> Optional[List[int]]:
        """
        Find shortest path between two entities using Dijkstra's algorithm.

        Args:
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            weight: Edge attribute to use as weight (default: 'weight')
                   Set to None for unweighted path

        Returns:
            List of entity IDs forming the shortest path, or None if no path exists

        Raises:
            ValueError: If graph not built or entities not in graph
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        if source_entity_id not in self.graph.nodes:
            raise ValueError(f"Source entity {source_entity_id} not in graph")

        if target_entity_id not in self.graph.nodes:
            raise ValueError(f"Target entity {target_entity_id} not in graph")

        try:
            # NetworkX uses inverted weights (lower = better), but our strength is
            # already 0-1 where higher = stronger. We invert it for pathfinding.
            if weight == 'weight':
                # Create inverted weight for pathfinding
                for u, v, data in self.graph.edges(data=True):
                    data['inv_weight'] = 1.0 - data.get('weight', 0.0)
                weight = 'inv_weight'

            path = nx.shortest_path(
                self.graph,
                source=source_entity_id,
                target=target_entity_id,
                weight=weight
            )

            logger.info(
                f"Path found: {' -> '.join([self.entity_id_to_name[nid] for nid in path])}"
            )

            return path

        except nx.NetworkXNoPath:
            logger.info(f"No path exists between {source_entity_id} and {target_entity_id}")
            return None

    def calculate_centrality_metrics(self) -> Dict[str, Dict[int, float]]:
        """
        Calculate various centrality metrics for all nodes.

        Centrality metrics measure the importance of nodes in the graph:
        - Degree centrality: Number of connections
        - Betweenness centrality: How often node appears on shortest paths
        - Closeness centrality: Average distance to all other nodes
        - Eigenvector centrality: Connections to important nodes

        Returns:
            Dictionary of centrality metrics:
            {
                'degree': {entity_id: score},
                'betweenness': {entity_id: score},
                'closeness': {entity_id: score},
                'eigenvector': {entity_id: score}
            }

        Raises:
            ValueError: If graph not built
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        logger.info("Calculating centrality metrics")

        metrics = {}

        # Degree centrality (normalized by max possible degree)
        metrics['degree'] = nx.degree_centrality(self.graph)

        # Betweenness centrality (normalized)
        metrics['betweenness'] = nx.betweenness_centrality(
            self.graph,
            weight='inv_weight' if 'inv_weight' in self.graph.edges[next(iter(self.graph.edges))] else None
        )

        # Closeness centrality (normalized)
        # Only works on connected graphs, so we handle disconnected components
        if nx.is_connected(self.graph):
            metrics['closeness'] = nx.closeness_centrality(self.graph)
        else:
            # Calculate for each component separately
            metrics['closeness'] = {}
            for component in nx.connected_components(self.graph):
                subgraph = self.graph.subgraph(component)
                closeness = nx.closeness_centrality(subgraph)
                metrics['closeness'].update(closeness)

        # Eigenvector centrality (connections to important nodes)
        try:
            metrics['eigenvector'] = nx.eigenvector_centrality(
                self.graph,
                max_iter=100,
                weight='weight'
            )
        except nx.PowerIterationFailedConvergence:
            logger.warning("Eigenvector centrality failed to converge, using PageRank instead")
            metrics['eigenvector'] = nx.pagerank(self.graph, weight='weight')

        logger.info("Centrality metrics calculated")

        return metrics

    def calculate_clustering_coefficient(self) -> Dict[int, float]:
        """
        Calculate clustering coefficient for each node.

        Clustering coefficient measures how much neighbors of a node
        are connected to each other (triangles in the graph).

        Returns:
            Dictionary mapping entity_id to clustering coefficient (0.0-1.0)

        Raises:
            ValueError: If graph not built
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        logger.info("Calculating clustering coefficients")

        clustering = nx.clustering(self.graph, weight='weight')

        logger.info(f"Average clustering coefficient: {nx.average_clustering(self.graph):.3f}")

        return clustering

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive graph statistics.

        Returns:
            Dictionary with graph statistics:
            {
                'nodes': int,
                'edges': int,
                'density': float,
                'components': int,
                'avg_degree': float,
                'avg_clustering': float,
                'diameter': int (if connected),
                'radius': int (if connected)
            }

        Raises:
            ValueError: If graph not built
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        logger.info("Calculating graph statistics")

        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'components': nx.number_connected_components(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'avg_clustering': nx.average_clustering(self.graph)
        }

        # Diameter and radius only for connected graphs
        if nx.is_connected(self.graph):
            stats['diameter'] = nx.diameter(self.graph)
            stats['radius'] = nx.radius(self.graph)
        else:
            # Calculate for largest component
            largest_cc = max(nx.connected_components(self.graph), key=len)
            subgraph = self.graph.subgraph(largest_cc)
            stats['diameter'] = nx.diameter(subgraph)
            stats['radius'] = nx.radius(subgraph)
            stats['largest_component_size'] = len(largest_cc)

        logger.info(f"Graph statistics: {stats}")

        return stats

    def export_to_dict(
        self,
        include_communities: bool = True,
        include_centrality: bool = True,
        include_clustering: bool = True
    ) -> Dict[str, Any]:
        """
        Export graph to dictionary format for API responses.

        Args:
            include_communities: Include community detection results
            include_centrality: Include centrality metrics
            include_clustering: Include clustering coefficients

        Returns:
            Dictionary with nodes, edges, and optional metrics:
            {
                'nodes': [
                    {
                        'id': int,
                        'name': str,
                        'type': str,
                        'occurrence_count': int,
                        'community': int (optional),
                        'centrality': {...} (optional),
                        'clustering': float (optional)
                    }
                ],
                'edges': [
                    {
                        'source': int,
                        'target': int,
                        'weight': float,
                        'co_occurrence_count': int
                    }
                ],
                'statistics': {...}
            }

        Raises:
            ValueError: If graph not built
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        logger.info("Exporting graph to dictionary")

        result = {
            'nodes': [],
            'edges': [],
            'statistics': self.get_graph_statistics()
        }

        # Get optional metrics
        communities = self.detect_communities() if include_communities else {}
        centrality = self.calculate_centrality_metrics() if include_centrality else {}
        clustering = self.calculate_clustering_coefficient() if include_clustering else {}

        # Export nodes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]

            node_dict = {
                'id': node_id,
                'name': node_data['name'],
                'type': node_data['entity_type'],
                'occurrence_count': node_data['occurrence_count']
            }

            if include_communities:
                node_dict['community'] = communities.get(node_id, 0)

            if include_centrality:
                node_dict['centrality'] = {
                    'degree': centrality['degree'].get(node_id, 0.0),
                    'betweenness': centrality['betweenness'].get(node_id, 0.0),
                    'closeness': centrality['closeness'].get(node_id, 0.0),
                    'eigenvector': centrality['eigenvector'].get(node_id, 0.0)
                }

            if include_clustering:
                node_dict['clustering'] = clustering.get(node_id, 0.0)

            result['nodes'].append(node_dict)

        # Export edges
        for source, target, edge_data in self.graph.edges(data=True):
            result['edges'].append({
                'source': source,
                'target': target,
                'weight': edge_data['weight'],
                'co_occurrence_count': edge_data['co_occurrence_count']
            })

        logger.info(f"Exported {len(result['nodes'])} nodes, {len(result['edges'])} edges")

        return result

    def get_entity_neighbors(
        self,
        entity_id: int,
        depth: int = 1,
        min_weight: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get neighbors of an entity up to specified depth.

        Args:
            entity_id: Entity ID to get neighbors for
            depth: How many hops to explore (1 = direct neighbors)
            min_weight: Minimum edge weight to consider

        Returns:
            List of neighbor dictionaries:
            [
                {
                    'id': int,
                    'name': str,
                    'distance': int,
                    'path_weight': float
                }
            ]

        Raises:
            ValueError: If graph not built or entity not in graph
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")

        if entity_id not in self.graph.nodes:
            raise ValueError(f"Entity {entity_id} not in graph")

        logger.info(f"Getting neighbors for entity {entity_id} (depth={depth})")

        neighbors = []

        # BFS to find neighbors at each depth level
        visited = {entity_id}
        current_level = {entity_id}

        for d in range(1, depth + 1):
            next_level = set()

            for node in current_level:
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        edge_data = self.graph[node][neighbor]
                        if edge_data['weight'] >= min_weight:
                            neighbors.append({
                                'id': neighbor,
                                'name': self.entity_id_to_name[neighbor],
                                'distance': d,
                                'path_weight': edge_data['weight']
                            })
                            visited.add(neighbor)
                            next_level.add(neighbor)

            current_level = next_level

        logger.info(f"Found {len(neighbors)} neighbors")

        return neighbors
