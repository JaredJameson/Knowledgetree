/**
 * KnowledgeTree Knowledge Graph Page
 * Interactive knowledge graph visualization with entity exploration
 * Phase 3: Knowledge Graph Visualization
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { projectsApi } from '@/lib/api';
import graphApi from '@/lib/api/graphApi';
import type { Project, KnowledgeGraphResponse, GraphNode } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { GraphVisualization } from '@/components/graph/GraphVisualization';
import { EntityDetailsPanel } from '@/components/graph/EntityDetailsPanel';
import {
  Loader2,
  Network,
  RefreshCw,
} from 'lucide-react';

export function KnowledgeGraphPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Graph state
  const [graphData, setGraphData] = useState<KnowledgeGraphResponse | null>(null);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [error, setError] = useState('');

  // Entity selection state
  const [selectedEntity, setSelectedEntity] = useState<GraphNode | null>(null);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load graph when project selected
  useEffect(() => {
    if (selectedProjectId) {
      loadGraph();
    }
  }, [selectedProjectId]);

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await projectsApi.list();
      setProjects(response.data.projects);

      // Auto-select first project if available
      if (response.data.projects.length > 0 && !selectedProjectId) {
        setSelectedProjectId(response.data.projects[0].id);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError(t('errors.loadProjectsFailed'));
    } finally {
      setLoadingProjects(false);
    }
  };

  const loadGraph = async () => {
    if (!selectedProjectId) return;

    try {
      setLoadingGraph(true);
      setError('');

      const response = await graphApi.buildGraph(selectedProjectId, {
        min_strength: 0.0,
        include_isolated: false,
        include_communities: true,
        include_centrality: true,
        include_clustering: true,
      });

      setGraphData(response.data);
    } catch (err) {
      console.error('Failed to load graph:', err);
      setError(t('errors.loadGraphFailed'));
    } finally {
      setLoadingGraph(false);
    }
  };

  const handleEntitySelect = (node: GraphNode) => {
    setSelectedEntity(node);
  };

  const handleEntityDeselect = () => {
    setSelectedEntity(null);
  };

  const handleRefresh = () => {
    loadGraph();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Network className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {t('graph.title')}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Project Selector */}
          {!loadingProjects && projects.length > 0 && (
            <Select
              value={selectedProjectId?.toString() || ''}
              onValueChange={(value) => setSelectedProjectId(parseInt(value))}
            >
              <SelectTrigger className="w-[250px]">
                <SelectValue placeholder={t('graph.selectProject')} />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id.toString()}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {/* Refresh Button */}
          {selectedProjectId && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loadingGraph}
            >
              <RefreshCw className={`h-4 w-4 ${loadingGraph ? 'animate-spin' : ''}`} />
            </Button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div>
        {loadingProjects ? (
          <div className="flex items-center justify-center h-96">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : projects.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>{t('graph.noProjects')}</CardTitle>
              <CardDescription>{t('graph.createProjectFirst')}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => navigate('/projects')}>
                {t('graph.goToProjects')}
              </Button>
            </CardContent>
          </Card>
        ) : !selectedProjectId ? (
          <Card>
            <CardHeader>
              <CardTitle>{t('graph.selectProjectTitle')}</CardTitle>
              <CardDescription>{t('graph.selectProjectDescription')}</CardDescription>
            </CardHeader>
          </Card>
        ) : error ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-red-600">{t('common.error')}</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={handleRefresh}>{t('common.retry')}</Button>
            </CardContent>
          </Card>
        ) : loadingGraph ? (
          <div className="flex flex-col items-center justify-center h-96 gap-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
            <p className="text-lg text-gray-600 dark:text-gray-300">
              {t('graph.buildingGraph')}
            </p>
          </div>
        ) : graphData ? (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Graph Visualization - Takes 3/4 width on large screens */}
            <div className="lg:col-span-3">
              <Card className="h-[calc(100vh-12rem)]">
                <CardContent className="p-0 h-full">
                  <GraphVisualization
                    graphData={graphData}
                    onNodeSelect={handleEntitySelect}
                    selectedNodeId={selectedEntity?.id}
                  />
                </CardContent>
              </Card>
            </div>

            {/* Entity Details Panel - Takes 1/4 width on large screens */}
            <div className="lg:col-span-1">
              <EntityDetailsPanel
                entity={selectedEntity}
                onClose={handleEntityDeselect}
              />
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default KnowledgeGraphPage;
