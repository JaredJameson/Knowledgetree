/**
 * KnowledgeTree - Agentic Workflows Page
 * AI-powered multi-agent workflows for complex research tasks
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Workflow,
  Play,
  Pause,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  Brain,
  Target,
  Layers,
  MessageSquare,
  Settings,
  FileText,
  Globe,
  Sparkles,
  Eye,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  ArrowRight,
} from 'lucide-react';
import { workflowsApi, projectsApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';

interface Project {
  id: number;
  name: string;
}

interface Workflow {
  id: number;
  name: string;
  status: 'pending' | 'processing' | 'awaiting_approval' | 'completed' | 'failed' | 'cancelled';
  task_type: string;
  current_step: string;
  current_agent: string;
  progress: {
    completed_steps: number;
    total_steps: number;
    percentage: number;
    current_operation: string;
  };
  agent_reasoning?: {
    agent: string;
    step: string;
    message: string;
    reasoning: string;
    timestamp: string;
  };
  created_at: string;
  updated_at: string;
}

export default function WorkflowsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [loading, setLoading] = useState(true);

  // New workflow form
  const [taskType, setTaskType] = useState<'research' | 'scraping' | 'analysis'>('research');
  const [userQuery, setUserQuery] = useState('');
  const [maxUrls, setMaxUrls] = useState(20);
  const [requireApproval, setRequireApproval] = useState(true);
  const [starting, setStarting] = useState(false);

  // URL candidates for approval
  const [urlCandidates, setUrlCandidates] = useState<any[]>([]);

  // Poll active workflows
  useEffect(() => {
    loadWorkflows();
    const interval = setInterval(() => {
      loadWorkflows();
    }, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Load projects
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await projectsApi.list(1, 100);
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadWorkflows = async () => {
    try {
      const response = await workflowsApi.list({ skip: 0, limit: 20 });
      setWorkflows(response.data.workflows || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartWorkflow = async () => {
    if (!userQuery.trim()) {
      toast({
        title: 'Błąd',
        description: 'Wprowadź opis zadania',
        variant: 'destructive',
      });
      return;
    }

    setStarting(true);

    try {
      const response = await workflowsApi.start({
        task_type: taskType,
        user_query: userQuery,
        config: {
          max_urls: maxUrls,
          require_approval: requireApproval,
        },
      });

      toast({
        title: 'Uruchomiono',
        description: `Workflow ID: ${response.data.workflow_id}`,
      });

      setUserQuery('');
      loadWorkflows();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Nie udało się uruchomić workflow';
      toast({
        title: 'Błąd',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setStarting(false);
    }
  };

  const handleSelectWorkflow = async (workflow: Workflow) => {
    setSelectedWorkflow(workflow);

    // Load URL candidates if awaiting approval
    if (workflow.status === 'awaiting_approval') {
      try {
        const response = await workflowsApi.getUrlCandidates(workflow.id);
        setUrlCandidates(response.data.candidates || []);
      } catch (error) {
        console.error('Failed to load URL candidates:', error);
      }
    }
  };

  const handleApprove = async (decision: 'approve' | 'reject' | 'modify') => {
    if (!selectedWorkflow) return;

    try {
      await workflowsApi.approve(selectedWorkflow.id, {
        decision,
        modifications: decision === 'modify' ? {
          add_urls: [],
          remove_urls: [],
          notes: 'User modifications'
        } : undefined,
      });

      toast({
        title: 'Zatwierdzono',
        description: `Workflow ${decision}ed`,
      });

      loadWorkflows();
      setUrlCandidates([]);
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Operacja nieudana',
        variant: 'destructive',
      });
    }
  };

  const handleStop = async (workflowId: number) => {
    try {
      await workflowsApi.stop(workflowId);
      toast({
        title: 'Zatrzymano',
        description: 'Workflow został zatrzymany',
      });
      loadWorkflows();
    } catch (error: any) {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się zatrzymać',
        variant: 'destructive',
      });
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-neutral-500',
      processing: 'bg-blue-500',
      awaiting_approval: 'bg-yellow-500',
      completed: 'bg-success-500',
      failed: 'bg-error-500',
      cancelled: 'bg-neutral-500',
    };
    return colors[status as keyof typeof colors] || 'bg-neutral-500';
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      pending: 'Oczekujący',
      processing: 'Przetwarzanie',
      awaiting_approval: 'Oczekuje zatwierdzenia',
      completed: 'Ukończony',
      failed: 'Błąd',
      cancelled: 'Anulowany',
    };
    return labels[status as keyof typeof labels] || status;
  };

  const getTaskTypeLabel = (type: string) => {
    const labels = {
      research: 'Badawczy',
      scraping: 'Crawling',
      analysis: 'Analityczny',
      full_pipeline: 'Pełny pipeline',
    };
    return labels[type as keyof typeof labels] || type;
  };

  const getTaskTypeIcon = (type: string) => {
    const icons = {
      research: <Target className="h-4 w-4" />,
      scraping: <Globe className="h-4 w-4" />,
      analysis: <Brain className="h-4 w-4" />,
      full_pipeline: <Layers className="h-4 w-4" />,
    };
    return icons[type as keyof typeof icons] || <Workflow className="h-4 w-4" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
            <Sparkles className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
              Agentic Workflows
            </h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Zautomatyzowane workflow oparte na agentach AI dla złożonych zadań
            </p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - New workflow and list */}
        <div className="lg:col-span-1 space-y-6">
          {/* New workflow card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5" />
                Nowy workflow
              </CardTitle>
              <CardDescription>
                Uruchom automatyczny workflow oparty na agentach AI
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Task type */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Typ zadania</label>
                <Select
                  value={taskType}
                  onValueChange={(value: any) => setTaskType(value)}
                  disabled={starting}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Wybierz typ zadania" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="research">
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 flex-shrink-0" />
                        <span>Badawczy</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="scraping">
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4 flex-shrink-0" />
                        <span>Web Scraping</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="analysis">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 flex-shrink-0" />
                        <span>Analityczny</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                {/* Selected type description */}
                <div className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-800 rounded-md px-3 py-2">
                  {taskType === 'research' && (
                    <>
                      <Target className="h-3.5 w-3.5 text-primary-500 flex-shrink-0" />
                      <span>Głęboka analiza tematu z wieloma źródłami</span>
                    </>
                  )}
                  {taskType === 'scraping' && (
                    <>
                      <Globe className="h-3.5 w-3.5 text-primary-500 flex-shrink-0" />
                      <span>Crawling URLi i ekstrakcja danych</span>
                    </>
                  )}
                  {taskType === 'analysis' && (
                    <>
                      <Brain className="h-3.5 w-3.5 text-primary-500 flex-shrink-0" />
                      <span>Analiza danych i generowanie wniosków</span>
                    </>
                  )}
                </div>
              </div>

              {/* User query */}
              <div>
                <label className="text-sm font-medium mb-2 block">Opis zadania</label>
                <Textarea
                  placeholder="Opisz co chcesz osiągnąć..."
                  value={userQuery}
                  onChange={(e) => setUserQuery(e.target.value)}
                  disabled={starting}
                  rows={4}
                />
              </div>

              {/* Options */}
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium">
                    Maks. URL: {maxUrls}
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="100"
                    value={maxUrls}
                    onChange={(e) => setMaxUrls(Number(e.target.value))}
                    disabled={starting}
                    className="w-full mt-1"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="approval"
                    checked={requireApproval}
                    onCheckedChange={(checked) => setRequireApproval(checked === true)}
                    disabled={starting}
                  />
                  <label htmlFor="approval" className="cursor-pointer text-sm">
                    Wymagaj zatwierdzenia URLi
                  </label>
                </div>
              </div>

              {/* Start button */}
              <Button
                onClick={handleStartWorkflow}
                disabled={starting || !userQuery.trim()}
                className="w-full"
                size="lg"
              >
                {starting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uruchamianie...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Uruchom workflow
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Workflows list */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Historia workflow</span>
                <Button variant="ghost" size="sm" onClick={loadWorkflows}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </CardTitle>
              <CardDescription>
                Kliknij workflow aby zobaczyć szczegóły po prawej →
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {workflows.length === 0 ? (
                  <p className="text-sm text-neutral-500 text-center py-4">
                    Brak workflow. Uruchom pierwszy!
                  </p>
                ) : (
                  workflows.map((workflow) => (
                    <div
                      key={workflow.id}
                      onClick={() => handleSelectWorkflow(workflow)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-800 ${
                        selectedWorkflow?.id === workflow.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-neutral-200 dark:border-neutral-700'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getTaskTypeIcon(workflow.task_type)}
                          <span className="font-medium text-sm line-clamp-1">
                            {workflow.name}
                          </span>
                        </div>
                        <Badge className={getStatusColor(workflow.status)} variant="secondary">
                          {getStatusLabel(workflow.status)}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-xs text-neutral-500">
                        <span>{getTaskTypeLabel(workflow.task_type)}</span>
                        <span>
                          {new Date(workflow.created_at).toLocaleString('pl-PL')}
                        </span>
                      </div>
                      {workflow.progress && (
                        <Progress
                          value={workflow.progress.percentage}
                          className="h-1 mt-2"
                        />
                      )}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right column - Workflow details */}
        <div className="lg:col-span-2">
          {selectedWorkflow ? (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {getTaskTypeIcon(selectedWorkflow.task_type)}
                      {selectedWorkflow.name}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      ID: {selectedWorkflow.id} • {getTaskTypeLabel(selectedWorkflow.task_type)}
                    </CardDescription>
                  </div>
                  <Badge className={getStatusColor(selectedWorkflow.status)} variant="secondary">
                    {getStatusLabel(selectedWorkflow.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="status" className="space-y-4">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="status">Status</TabsTrigger>
                    <TabsTrigger value="reasoning">Reasoning</TabsTrigger>
                    <TabsTrigger value="approval">Zatwierdzanie</TabsTrigger>
                    <TabsTrigger value="results">Wyniki</TabsTrigger>
                  </TabsList>

                  {/* Status tab */}
                  <TabsContent value="status" className="space-y-4">
                    {/* Progress */}
                    {selectedWorkflow.progress && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Postęp</span>
                          <span className="text-sm text-neutral-500">
                            {selectedWorkflow.progress.completed_steps} / {selectedWorkflow.progress.total_steps} kroków
                          </span>
                        </div>
                        <Progress value={selectedWorkflow.progress.percentage} />
                        <p className="text-xs text-neutral-500 mt-1">
                          {selectedWorkflow.progress.current_operation}
                        </p>
                      </div>
                    )}

                    {/* Current agent */}
                    {selectedWorkflow.current_agent && (
                      <div>
                        <span className="text-sm font-medium">Aktualny agent:</span>
                        <Badge variant="outline" className="ml-2">
                          {selectedWorkflow.current_agent}
                        </Badge>
                      </div>
                    )}

                    {/* Actions */}
                    {(selectedWorkflow.status === 'processing' ||
                      selectedWorkflow.status === 'awaiting_approval') && (
                      <Button
                        variant="destructive"
                        onClick={() => handleStop(selectedWorkflow.id)}
                      >
                        <Pause className="h-4 w-4 mr-2" />
                        Zatrzymaj workflow
                      </Button>
                    )}

                    {/* Timestamps */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-neutral-500">Utworzono:</span>
                        <p className="font-medium">
                          {new Date(selectedWorkflow.created_at).toLocaleString('pl-PL')}
                        </p>
                      </div>
                      <div>
                        <span className="text-neutral-500">Zaktualizowano:</span>
                        <p className="font-medium">
                          {new Date(selectedWorkflow.updated_at).toLocaleString('pl-PL')}
                        </p>
                      </div>
                    </div>
                  </TabsContent>

                  {/* Reasoning tab */}
                  <TabsContent value="reasoning" className="space-y-4">
                    {selectedWorkflow.agent_reasoning ? (
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 text-sm">
                          <Brain className="h-4 w-4 text-indigo-500" />
                          <span className="font-medium">
                            {selectedWorkflow.agent_reasoning.agent}
                          </span>
                          <span className="text-neutral-500">•</span>
                          <span className="text-neutral-500">
                            {selectedWorkflow.agent_reasoning.step}
                          </span>
                        </div>

                        <div>
                          <span className="text-sm font-medium">Decyzja:</span>
                          <p className="text-neutral-700 dark:text-neutral-300 mt-1">
                            {selectedWorkflow.agent_reasoning.message}
                          </p>
                        </div>

                        {selectedWorkflow.agent_reasoning.reasoning && (
                          <div>
                            <span className="text-sm font-medium">Uzasadnienie:</span>
                            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1 whitespace-pre-wrap">
                              {selectedWorkflow.agent_reasoning.reasoning}
                            </p>
                          </div>
                        )}

                        <p className="text-xs text-neutral-500">
                          {new Date(selectedWorkflow.agent_reasoning.timestamp).toLocaleString('pl-PL')}
                        </p>
                      </div>
                    ) : (
                      <p className="text-sm text-neutral-500 text-center py-4">
                        Brak danych reasoning dla tego workflow
                      </p>
                    )}
                  </TabsContent>

                  {/* Approval tab */}
                  <TabsContent value="approval" className="space-y-4">
                    {selectedWorkflow.status === 'awaiting_approval' ? (
                      <>
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            Workflow czeka na zatwierdzenie. Przejrzyj znalezione URL i
                            zdecyduj czy zatwierdzić czy odrzucić.
                          </AlertDescription>
                        </Alert>

                        {urlCandidates.length > 0 && (
                          <div>
                            <h3 className="font-medium mb-3">Kandydaci URL ({urlCandidates.length})</h3>
                            <div className="space-y-2 max-h-96 overflow-y-auto">
                              {urlCandidates.map((candidate) => (
                                <div
                                  key={candidate.id}
                                  className="p-3 border rounded-lg"
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <p className="font-medium text-sm line-clamp-1">
                                        {candidate.title || candidate.url}
                                      </p>
                                      <p className="text-xs text-neutral-500 truncate">
                                        {candidate.url}
                                      </p>
                                    </div>
                                    {candidate.relevance_score && (
                                      <Badge variant="secondary">
                                        {(candidate.relevance_score * 100).toFixed(0)}%
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleApprove('approve')}
                            className="flex-1"
                          >
                            <ThumbsUp className="h-4 w-4 mr-2" />
                            Zatwierdź
                          </Button>
                          <Button
                            onClick={() => handleApprove('reject')}
                            variant="destructive"
                            className="flex-1"
                          >
                            <ThumbsDown className="h-4 w-4 mr-2" />
                            Odrzuć
                          </Button>
                        </div>
                      </>
                    ) : selectedWorkflow.status === 'completed' ? (
                      <Alert>
                        <CheckCircle2 className="h-4 w-4" />
                        <AlertDescription>
                          Workflow został ukończony pomyślnie.
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          Workflow nie wymaga zatwierdzenia w tym momencie.
                        </AlertDescription>
                      </Alert>
                    )}
                  </TabsContent>

                  {/* Results tab */}
                  <TabsContent value="results" className="space-y-4">
                    {selectedWorkflow.status === 'completed' ? (
                      <Alert>
                        <CheckCircle2 className="h-4 w-4" />
                        <AlertDescription>
                          Workflow zakończony. Wyniki są dostępne.
                        </AlertDescription>
                      </Alert>
                    ) : selectedWorkflow.status === 'failed' ? (
                      <Alert variant="destructive">
                        <XCircle className="h-4 w-4" />
                        <AlertDescription>
                          Workflow zakończył się błędem.
                        </AlertDescription>
                      </Alert>
                    ) : (
                      <Alert>
                        <Clock className="h-4 w-4" />
                        <AlertDescription>
                          Wyniki będą dostępne po zakończeniu workflow.
                        </AlertDescription>
                      </Alert>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Eye className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">Wybierz workflow</h3>
                  <p className="text-neutral-500">
                    Wybierz workflow z listy po lewej stronie, aby zobaczyć szczegóły
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Info card */}
      <Card className="bg-indigo-50 dark:bg-indigo-950 border-indigo-200 dark:border-indigo-800 mt-6">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Sparkles className="h-5 w-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-indigo-800 dark:text-indigo-200">
              <p className="font-medium mb-1">Agentic Workflows</p>
              <p className="text-xs opacity-90">
                Automatyczne workflow wykorzystujące wiele agentów AI do realizacji
                złożonych zadań badawczych. Agenty współpracują, planują, crawlują dane
                i generują strukturyzowane wyniki.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
