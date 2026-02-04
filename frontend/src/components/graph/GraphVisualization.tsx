/**
 * Graph Visualization Component
 * Interactive knowledge graph using ReactFlow with dagre layout
 * Phase 3: Knowledge Graph Visualization
 */

import { useEffect, useCallback } from 'react';
import ReactFlow, {
  type Node,
  type Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  ConnectionLineType,
  Position,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import type { KnowledgeGraphResponse, GraphNode as APIGraphNode } from '@/types/api';

// Dagre graph layout configuration
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 180;
const nodeHeight = 80;

// Layout algorithm using dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction, ranksep: 150, nodesep: 100 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;

    // Shift to center
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes, edges };
};

// Community color palette
const communityColors = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#84cc16', // lime
  '#6366f1', // indigo
];

interface GraphVisualizationProps {
  graphData: KnowledgeGraphResponse;
  onNodeSelect?: (node: APIGraphNode) => void;
  selectedNodeId?: number;
}

export function GraphVisualization({
  graphData,
  onNodeSelect,
  selectedNodeId,
}: GraphVisualizationProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Convert API graph data to ReactFlow format
  useEffect(() => {
    if (!graphData) return;

    // Create nodes from API data
    const reactFlowNodes: Node[] = graphData.nodes.map((node) => {
      const communityColor = node.community !== undefined
        ? communityColors[node.community % communityColors.length]
        : '#6b7280';

      const isSelected = node.id === selectedNodeId;
      const degreeScore = node.centrality?.degree || 0;

      // Scale node size based on degree centrality
      const scaleFactor = 1 + (degreeScore * 0.5);
      const scaledWidth = nodeWidth * Math.min(scaleFactor, 1.5);
      const scaledHeight = nodeHeight * Math.min(scaleFactor, 1.2);

      return {
        id: node.id.toString(),
        type: 'default',
        position: { x: 0, y: 0 }, // Will be set by layout algorithm
        data: {
          label: node.name,
          node: node,
        },
        style: {
          background: isSelected ? communityColor : '#ffffff',
          color: isSelected ? '#ffffff' : '#1f2937',
          border: `2px solid ${communityColor}`,
          borderRadius: '8px',
          padding: '12px',
          fontSize: '13px',
          fontWeight: isSelected ? '600' : '500',
          width: scaledWidth,
          height: scaledHeight,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          boxShadow: isSelected
            ? `0 0 20px ${communityColor}80`
            : '0 2px 8px rgba(0,0,0,0.1)',
          transition: 'all 0.2s ease',
        },
      };
    });

    // Create edges from API data
    const reactFlowEdges: Edge[] = graphData.edges.map((edge, idx) => {
      // Edge thickness based on weight
      const strokeWidth = 1 + (edge.weight * 3);
      const opacity = 0.3 + (edge.weight * 0.5);

      return {
        id: `e${edge.source}-${edge.target}-${idx}`,
        source: edge.source.toString(),
        target: edge.target.toString(),
        type: ConnectionLineType.Bezier,
        animated: edge.weight > 0.7,
        style: {
          strokeWidth,
          stroke: `rgba(100, 116, 139, ${opacity})`,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: `rgba(100, 116, 139, ${opacity})`,
        },
        label: edge.weight > 0.5 ? `${(edge.weight * 100).toFixed(0)}%` : undefined,
        labelStyle: {
          fontSize: 10,
          fill: '#64748b',
          fontWeight: 600,
        },
        labelBgStyle: {
          fill: '#ffffff',
          fillOpacity: 0.8,
        },
      };
    });

    // Apply dagre layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      reactFlowNodes,
      reactFlowEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [graphData, selectedNodeId]);

  // Handle node click
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (onNodeSelect && node.data.node) {
        onNodeSelect(node.data.node);
      }
    },
    [onNodeSelect]
  );

  // Minimap node color based on community
  const minimapNodeColor = useCallback((node: Node) => {
    const apiNode = node.data.node as APIGraphNode;
    if (apiNode.community !== undefined) {
      return communityColors[apiNode.community % communityColors.length];
    }
    return '#6b7280';
  }, []);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: ConnectionLineType.Bezier,
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={minimapNodeColor}
          maskColor="rgba(0, 0, 0, 0.1)"
          position="bottom-right"
        />
      </ReactFlow>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 max-w-xs z-10">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
          Graph Statistics
        </h3>
        <div className="space-y-1 text-xs text-gray-600 dark:text-gray-300">
          <div className="flex justify-between">
            <span>Nodes:</span>
            <span className="font-medium">{graphData.statistics.nodes}</span>
          </div>
          <div className="flex justify-between">
            <span>Edges:</span>
            <span className="font-medium">{graphData.statistics.edges}</span>
          </div>
          <div className="flex justify-between">
            <span>Density:</span>
            <span className="font-medium">
              {(graphData.statistics.density * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>Components:</span>
            <span className="font-medium">{graphData.statistics.components}</span>
          </div>
          <div className="flex justify-between">
            <span>Avg Degree:</span>
            <span className="font-medium">
              {graphData.statistics.avg_degree.toFixed(1)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
