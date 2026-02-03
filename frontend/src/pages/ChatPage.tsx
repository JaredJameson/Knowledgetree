/**
 * KnowledgeTree Chat Page
 * RAG-powered AI chat with source citations
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { useAuth } from '@/context/AuthContext';
import { projectsApi, chatApi, artifactsApi } from '@/lib/api';
import type { Project, Conversation, Message, RetrievedChunk } from '@/types/api';
import type { Artifact } from '@/types/artifact';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import ArtifactPanel from '@/components/ArtifactPanel';

// Extended Message type with sources and artifact for chat display
interface ChatMessage extends Message {
  sources?: RetrievedChunk[];
  artifactId?: number;
}
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { LanguageSwitcher } from '@/components/language-switcher';
import { ThemeToggle } from '@/components/theme-toggle';
import {
  Loader2,
  MessageSquare,
  ChevronLeft,
  Send,
  Plus,
  Trash2,
  Copy,
  Check,
  Bot,
  User,
  Sparkles,
  Menu,
  X,
  AlertCircle,
  RefreshCw,
  Clock
} from 'lucide-react';

export function ChatPage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Conversations state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [loadingConversations, setLoadingConversations] = useState(false);

  // Messages state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [lastFailedMessage, setLastFailedMessage] = useState<string>('');

  // Chat settings
  const [useRag, setUseRag] = useState(true);
  const [maxContextChunks, setMaxContextChunks] = useState(5);

  // Agent Mode state
  const [agentMode, setAgentMode] = useState(false);
  const [agentUrl, setAgentUrl] = useState('');
  const [agentStatus, setAgentStatus] = useState<'idle' | 'crawling' | 'generating' | 'done'>('idle');
  const [agentProgress, setAgentProgress] = useState<string>('');

  // UI state
  const [copiedMessageId, setCopiedMessageId] = useState<number | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteConversation, setDeleteConversation] = useState<Conversation | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Artifact Panel state
  const [artifactPanelOpen, setArtifactPanelOpen] = useState(false);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [loadingArtifact, setLoadingArtifact] = useState(false);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load conversations when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadConversations();
    } else {
      setConversations([]);
      setSelectedConversationId(null);
    }
  }, [selectedProjectId]);

  // Load messages when conversation changes
  useEffect(() => {
    if (selectedConversationId) {
      loadConversation();
    } else {
      setMessages([]);
    }
  }, [selectedConversationId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await projectsApi.list();
      const projectsData = response.data.projects || response.data || [];
      setProjects(projectsData);

      // Auto-select first project
      if (projectsData.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projectsData[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('chat.errors.loadProjectsFailed'));
    } finally {
      setLoadingProjects(false);
    }
  };

  const loadConversations = async () => {
    if (!selectedProjectId) return;

    try {
      setLoadingConversations(true);
      const response = await chatApi.listConversations(selectedProjectId);
      const conversationsData = response.data.conversations || response.data || [];
      setConversations(conversationsData);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoadingConversations(false);
    }
  };

  const loadConversation = async () => {
    if (!selectedConversationId) return;

    try {
      const response = await chatApi.getConversation(selectedConversationId);
      setMessages(response.data.messages || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
    }
  };

  const handleNewConversation = () => {
    setSelectedConversationId(null);
    setMessages([]);
    setInputMessage('');
    setMobileMenuOpen(false);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();

    // Agent Mode validation
    if (agentMode && !agentUrl.trim()) {
      setError('Wpisz URL do crawlowania w trybie Agent Mode');
      return;
    }

    if (!inputMessage.trim()) {
      setError(t('chat.errors.noMessage'));
      return;
    }

    if (!selectedProjectId) {
      setError(t('chat.errors.noProject'));
      return;
    }

    try {
      setSending(true);
      setError('');

      // Set agent status if in agent mode
      if (agentMode) {
        setAgentStatus('crawling');
        setAgentProgress('Przygotowywanie...');
      }

      // Add user message immediately
      const userMessage: ChatMessage = {
        id: Date.now(),
        role: 'user',
        content: agentMode
          ? `🌐 ${agentUrl}\n\n${inputMessage.trim()}`
          : inputMessage.trim(),
        created_at: new Date().toISOString(),
        tokens_used: null,
      };

      setMessages([...messages, userMessage]);

      // Create placeholder for assistant message (streaming)
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        tokens_used: null,
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Track streaming state
      let retrievedChunks: RetrievedChunk[] = [];
      let streamedContent = '';

      // Use fetch for streaming
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8765';
      const token = localStorage.getItem('access_token');

      const requestBody: any = {
        message: inputMessage.trim(),
        project_id: selectedProjectId,
        conversation_id: selectedConversationId || undefined,
        use_rag: useRag,
        max_context_chunks: maxContextChunks,
      };

      // Add agent mode fields
      if (agentMode) {
        requestBody.agent_mode = true;
        requestBody.agent_url = agentUrl.trim();
      }

      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Parse SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No response body');

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const event = JSON.parse(data);

              if (event.type === 'token') {
                // Append token to message
                streamedContent += event.content;
                setMessages(prev => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg?.role === 'assistant') {
                    lastMsg.content = streamedContent;
                  }
                  return updated;
                });
              } else if (event.type === 'chunk') {
                // Track retrieved chunk
                retrievedChunks.push({
                  chunk_id: event.chunk_id,
                  document_id: event.document_id,
                  document_title: event.document_title,
                  document_filename: event.document_filename,
                  chunk_text: '',
                  similarity_score: event.similarity_score,
                });
              } else if (event.type === 'agent_status') {
                // Update agent status
                if (event.status === 'crawling') {
                  setAgentStatus('crawling');
                  setAgentProgress(event.message || 'Crawling w toku...');
                } else if (event.status === 'generating') {
                  setAgentStatus('generating');
                  setAgentProgress(event.message || 'Generowanie drzewa...');
                } else if (event.status === 'done') {
                  setAgentStatus('done');
                  setAgentProgress(event.message || 'Zakończono!');
                }
              } else if (event.type === 'artifact_created') {
                // Auto-open artifact panel when artifact is created
                const artifactId = event.artifact_id;
                if (artifactId) {
                  try {
                    setLoadingArtifact(true);
                    const artifactResponse = await artifactsApi.get(artifactId);
                    const artifact = artifactResponse.data;
                    setSelectedArtifact(artifact);
                    setArtifactPanelOpen(true);
                    setLoadingArtifact(false);
                  } catch (artifactError) {
                    console.error('Failed to load artifact:', artifactError);
                    setLoadingArtifact(false);
                  }
                }
              } else if (event.type === 'done') {
                // Update with final metadata
                setMessages(prev => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg?.role === 'assistant') {
                    lastMsg.tokens_used = event.tokens_used;
                    lastMsg.sources = retrievedChunks;
                  }
                  return updated;
                });

                // Reset agent status after completion
                if (agentMode) {
                  setTimeout(() => {
                    setAgentStatus('idle');
                    setAgentProgress('');
                  }, 3000);
                }
              } else if (event.type === 'error') {
                setError(event.message || t('chat.errors.sendFailed'));
                setLastFailedMessage(inputMessage.trim());
                if (agentMode) {
                  setAgentStatus('idle');
                  setAgentProgress('');
                }
              }
            } catch (parseError) {
              console.error('Failed to parse SSE event:', parseError);
            }
          }
        }
      }

      setInputMessage('');

      // Update conversation ID if new conversation was created
      // Note: The backend creates the conversation, but we don't get the ID in streaming
      // We'll need to reload conversations to get the new ID
      if (!selectedConversationId) {
        await loadConversations();
        // The newest conversation should be the one we just created
        if (conversations.length > 0) {
          setSelectedConversationId(conversations[0].id);
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : t('chat.errors.sendFailed'));
      setLastFailedMessage(inputMessage.trim());
      // Remove the placeholder assistant message on error
      setMessages(prev => prev.slice(0, -1));
      if (agentMode) {
        setAgentStatus('idle');
        setAgentProgress('');
      }
    } finally {
      setSending(false);
    }
  };

  const handleCopyMessage = (messageId: number, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMessageId(messageId);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const openDeleteDialog = (conversation: Conversation) => {
    setDeleteConversation(conversation);
    setDeleteOpen(true);
  };

  const handleDeleteConversation = async () => {
    if (!deleteConversation) return;

    try {
      setDeleteLoading(true);
      await chatApi.deleteConversation(deleteConversation.id);
      setDeleteOpen(false);

      // Clear selection if deleted conversation was selected
      if (selectedConversationId === deleteConversation.id) {
        setSelectedConversationId(null);
        setMessages([]);
      }

      await loadConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('chat.errors.deleteFailed'));
    } finally {
      setDeleteLoading(false);
    }
  };

  // Artifact handlers
  const handleViewArtifact = async (artifactId: number) => {
    try {
      setLoadingArtifact(true);
      const response = await artifactsApi.get(artifactId);
      setSelectedArtifact(response.data);
      setArtifactPanelOpen(true);
    } catch (err) {
      console.error('Failed to load artifact:', err);
      setError(err instanceof Error ? err.message : t('chat.errors.loadArtifactFailed'));
    } finally {
      setLoadingArtifact(false);
    }
  };

  const handleArtifactUpdate = (updatedArtifact: Artifact) => {
    setSelectedArtifact(updatedArtifact);
  };

  const handleArtifactDelete = (artifactId: number) => {
    // Remove artifact reference from messages
    setMessages(messages.map(msg =>
      msg.artifactId === artifactId ? { ...msg, artifactId: undefined } : msg
    ));
    setSelectedArtifact(null);
    setArtifactPanelOpen(false);
  };

  const handleArtifactRegenerate = async (newArtifact: Artifact) => {
    setSelectedArtifact(newArtifact);
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Dashboard
              </Button>
              <div className="h-8 w-px bg-neutral-200 dark:bg-neutral-800" />
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
                {t('app.name')}
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <Select
                value={selectedProjectId?.toString()}
                onValueChange={(value: string) => setSelectedProjectId(parseInt(value))}
                disabled={loadingProjects}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder={t('chat.selectProject')} />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id.toString()}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                {user?.email}
              </span>
              <LanguageSwitcher />
              <ThemeToggle />
              <Button variant="outline" onClick={logout}>
                {t('common.signOut')}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      {!selectedProjectId ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <Card className="text-center max-w-md">
            <CardContent className="pt-6">
              <MessageSquare className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
                {t('chat.noProjectSelected')}
              </h3>
              <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                {t('chat.noProjectSelectedDescription')}
              </p>
              <Button onClick={() => navigate('/projects')}>
                {t('documents.backToProjects')}
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar - Conversations */}
          <div className={`
            fixed inset-y-0 left-0 z-50 w-64
            md:relative md:z-0
            transform transition-transform duration-300 ease-in-out
            ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
            border-r border-neutral-200 dark:border-neutral-800
            bg-white dark:bg-neutral-950 flex flex-col
          `}>
            <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden flex-shrink-0"
                onClick={() => setMobileMenuOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
              <Button
                onClick={handleNewConversation}
                className="flex-1"
                size="sm"
              >
                <Plus className="mr-2 h-4 w-4" />
                {t('chat.newConversation')}
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {loadingConversations ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="p-3 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 px-4">
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {t('chat.noConversations')}
                  </p>
                </div>
              ) : (
                <div className="space-y-1">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`
                        group p-3 rounded cursor-pointer transition-colors
                        ${selectedConversationId === conv.id
                          ? 'bg-primary-50 dark:bg-primary-900/20'
                          : 'hover:bg-neutral-100 dark:hover:bg-neutral-800'
                        }
                      `}
                      onClick={() => {
                        setSelectedConversationId(conv.id);
                        setMobileMenuOpen(false);
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50 truncate">
                            {conv.title || t('chat.conversation.defaultTitle')}
                          </p>
                          <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                            {conv.message_count || 0} {t('chat.messages.user').toLowerCase()}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 group-hover:opacity-100 h-8 w-8 p-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            openDeleteDialog(conv);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Settings */}
            <div className="p-4 border-t border-neutral-200 dark:border-neutral-800">
              <div className="space-y-3">
                {/* Agent Mode Toggle */}
                <div className="flex items-center justify-between">
                  <Label htmlFor="agent-mode" className="text-xs font-medium text-primary-600 dark:text-primary-400">
                    🤖 Agent Mode
                  </Label>
                  <input
                    id="agent-mode"
                    type="checkbox"
                    checked={agentMode}
                    onChange={(e) => {
                      setAgentMode(e.target.checked);
                      if (!e.target.checked) {
                        setAgentUrl('');
                        setAgentStatus('idle');
                        setAgentProgress('');
                      }
                    }}
                    className="rounded"
                  />
                </div>

                {/* Agent Mode URL Input */}
                {agentMode && (
                  <div className="space-y-1 p-2 bg-primary-50 dark:bg-primary-900/20 rounded border border-primary-200 dark:border-primary-800">
                    <Label htmlFor="agent-url" className="text-xs">
                      URL do crawlowania:
                    </Label>
                    <Input
                      id="agent-url"
                      type="url"
                      placeholder="https://example.com"
                      value={agentUrl}
                      onChange={(e) => setAgentUrl(e.target.value)}
                      className="h-8 text-xs"
                      disabled={sending}
                    />
                    <p className="text-xs text-neutral-600 dark:text-neutral-400">
                      Agent pobierze treść i utworzy drzewo kategorii
                    </p>
                  </div>
                )}

                <div className="border-t border-neutral-200 dark:border-neutral-800 pt-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="use-rag" className="text-xs">
                      {t('chat.settings.useRag')}
                    </Label>
                    <input
                      id="use-rag"
                      type="checkbox"
                      checked={useRag}
                      onChange={(e) => setUseRag(e.target.checked)}
                      className="rounded"
                    />
                  </div>
                  {useRag && (
                    <div className="space-y-1">
                      <Label htmlFor="max-chunks" className="text-xs">
                        {t('chat.settings.contextChunks')}
                      </Label>
                      <Input
                        id="max-chunks"
                        type="number"
                        min="1"
                        max="10"
                        value={maxContextChunks}
                        onChange={(e) => setMaxContextChunks(parseInt(e.target.value))}
                        className="h-8"
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Menu Backdrop */}
          {mobileMenuOpen && (
            <div
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setMobileMenuOpen(false)}
            />
          )}

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <MessageSquare className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                    <p className="text-neutral-600 dark:text-neutral-400">
                      {t('chat.messages.empty')}
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.role === 'assistant' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                            <Bot className="h-5 w-5 text-white" />
                          </div>
                        </div>
                      )}

                      <div
                        className={`max-w-2xl ${
                          message.role === 'user'
                            ? 'bg-primary-600 text-white'
                            : 'bg-white dark:bg-neutral-800'
                        } rounded-lg p-4 shadow-sm`}
                      >
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          {message.role === 'user' ? (
                            <p className="text-white">{message.content}</p>
                          ) : (
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                code({ node, className, children, ...props }: any) {
                                  const match = /language-(\w+)/.exec(className || '');
                                  const inline = !match;
                                  return !inline && match ? (
                                    <SyntaxHighlighter
                                      style={oneDark as any}
                                      language={match[1]}
                                      PreTag="div"
                                      {...props}
                                    >
                                      {String(children).replace(/\n$/, '')}
                                    </SyntaxHighlighter>
                                  ) : (
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  );
                                },
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          )}
                        </div>

                        {/* Timestamp */}
                        {message.created_at && (
                          <div className={`flex items-center gap-1 mt-2 text-xs ${
                            message.role === 'user'
                              ? 'text-white/70'
                              : 'text-neutral-500 dark:text-neutral-400'
                          }`}>
                            <Clock className="h-3 w-3" />
                            <span>
                              {new Date(message.created_at).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        )}

                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
                            <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-2">
                              {t('chat.sources.used', { count: message.sources.length })}
                            </p>
                            <div className="space-y-2">
                              {message.sources.map((source, idx) => (
                                <div
                                  key={idx}
                                  className="text-xs p-2 bg-neutral-50 dark:bg-neutral-900 rounded"
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="font-medium text-neutral-900 dark:text-neutral-50">
                                      {source.document_title}
                                    </span>
                                    <Badge variant="secondary" className="text-xs">
                                      {(source.similarity_score * 100).toFixed(0)}%
                                    </Badge>
                                  </div>
                                  <p className="text-neutral-600 dark:text-neutral-400 line-clamp-2">
                                    {source.chunk_text}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="mt-2 flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={() => handleCopyMessage(message.id, message.content)}
                          >
                            {copiedMessageId === message.id ? (
                              <>
                                <Check className="h-3 w-3 mr-1" />
                                {t('chat.actions.copied')}
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3 mr-1" />
                                {t('chat.actions.copy')}
                              </>
                            )}
                          </Button>

                          {/* View Artifact Button */}
                          {message.artifactId && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2 text-xs text-primary-600 hover:text-primary-700"
                              onClick={() => handleViewArtifact(message.artifactId!)}
                              disabled={loadingArtifact}
                            >
                              {loadingArtifact ? (
                                <>
                                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                  {t('common.loading')}
                                </>
                              ) : (
                                <>
                                  <Sparkles className="h-3 w-3 mr-1" />
                                  {t('chat.actions.viewArtifact', 'View Artifact')}
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      </div>

                      {message.role === 'user' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-neutral-600 flex items-center justify-center">
                            <User className="h-5 w-5 text-white" />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}

                  {sending && (
                    <div className="flex gap-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                          <Bot className="h-5 w-5 text-white" />
                        </div>
                      </div>
                      <div className="bg-white dark:bg-neutral-800 rounded-lg p-4 shadow-sm max-w-2xl">
                        <div className="space-y-2">
                          <Skeleton className="h-4 w-full" />
                          <Skeleton className="h-4 w-5/6" />
                          <Skeleton className="h-4 w-4/6" />
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="px-4 py-2 border-t border-neutral-200 dark:border-neutral-800">
                <Alert variant="destructive" className="relative">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>{t('chat.errors.title', 'Error')}</AlertTitle>
                  <AlertDescription className="flex items-center justify-between gap-4">
                    <span>{error}</span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {lastFailedMessage && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7"
                          onClick={() => {
                            setInputMessage(lastFailedMessage);
                            setError('');
                            setLastFailedMessage('');
                          }}
                        >
                          <RefreshCw className="h-3 w-3 mr-1" />
                          {t('chat.actions.retry', 'Retry')}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => {
                          setError('');
                          setLastFailedMessage('');
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              </div>
            )}

            {/* Input Area */}
            <div className="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 p-4">
              {/* Agent Status Indicator */}
              {agentStatus !== 'idle' && (
                <div className="mb-2 p-2 bg-primary-50 dark:bg-primary-900/20 rounded border border-primary-200 dark:border-primary-800">
                  <div className="flex items-center gap-2 text-sm text-primary-700 dark:text-primary-300">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>
                      {agentStatus === 'crawling' && '🔍 Crawling strony...'}
                      {agentStatus === 'generating' && '🧠 Generowanie drzewa wiedzy...'}
                      {agentStatus === 'done' && '✅ Gotowe!'}
                    </span>
                  </div>
                  {agentProgress && (
                    <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">{agentProgress}</p>
                  )}
                </div>
              )}

              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={agentMode
                    ? (agentUrl ? "Opisz czego mam szukać na stronie..." : "Wpisz URL do crawlowania powyżej")
                    : t('chat.inputPlaceholder')
                  }
                  disabled={sending || (agentMode && !agentUrl)}
                  rows={1}
                  className="flex-1 resize-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                />
                <Button
                  type="submit"
                  disabled={sending || !inputMessage.trim() || (agentMode && !agentUrl)}
                  size="lg"
                  className={agentMode ? "bg-primary-600 hover:bg-primary-700" : ""}
                >
                  {sending ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : agentMode ? (
                    <Sparkles className="h-5 w-5" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Conversation Dialog */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('chat.conversation.delete')}</AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>{t('chat.conversation.deleteConfirm')}</p>
              {deleteConversation && (
                <p className="font-medium text-neutral-900 dark:text-neutral-50">
                  {deleteConversation.title || t('chat.conversation.defaultTitle')}
                </p>
              )}
              <p className="text-error-600 dark:text-error-400">
                {t('chat.conversation.deleteWarning')}
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteLoading}>
              {t('common.cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConversation}
              disabled={deleteLoading}
              className="bg-error-600 hover:bg-error-700 dark:bg-error-700 dark:hover:bg-error-800"
            >
              {deleteLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {deleteLoading ? t('chat.conversation.deleting') : t('common.delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Artifact Panel */}
      <ArtifactPanel
        artifact={selectedArtifact}
        isOpen={artifactPanelOpen}
        onClose={() => setArtifactPanelOpen(false)}
        onUpdate={handleArtifactUpdate}
        onDelete={handleArtifactDelete}
        onRegenerate={handleArtifactRegenerate}
      />
    </div>
  );
}
