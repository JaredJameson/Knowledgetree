/**
 * KnowledgeTree Documents Page
 * Upload and manage documents with processing pipeline
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDropzone } from 'react-dropzone';
import { useAuth } from '@/context/AuthContext';
import { projectsApi, documentsApi, exportApi } from '@/lib/api';
import { downloadBlob } from '@/lib/download';
import type { Project, Document, ProcessingStatus, GenerateTreeResponse } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
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
import { AgenticCrawlDialog } from '@/components/AgenticCrawlDialog';
import {
  Loader2,
  Upload,
  FileText,
  ChevronLeft,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  FolderTree,
  Download
} from 'lucide-react';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function DocumentsPage() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Documents state
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [error, setError] = useState('');

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Processing state
  const [processingDocId, setProcessingDocId] = useState<number | null>(null);
  
  // Progress tracking state
  const [documentProgress, setDocumentProgress] = useState<Record<number, {
    percentage: number;
    step: string;
    message: string;
    status: string;
  }>>({});

  // Delete dialog state
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteDocument, setDeleteDocument] = useState<Document | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Generate tree state
  const [generatingTreeDocId, setGeneratingTreeDocId] = useState<number | null>(null);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load documents when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadDocuments();
    } else {
      setDocuments([]);
    }
  }, [selectedProjectId]);

  // Auto-reconnect SSE for processing documents after page refresh
  useEffect(() => {
    const eventSources: Map<number, EventSource> = new Map();

    documents.forEach(doc => {
      if (doc.processing_status?.toLowerCase() === 'processing') {
        console.log(`🔄 Auto-connecting SSE for document ${doc.id} (status: ${doc.processing_status})`);

        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8765';
        const token = localStorage.getItem('access_token');
        const streamUrl = `${API_BASE_URL}/api/v1/documents/${doc.id}/progress/stream?token=${token}`;

        const eventSource = new EventSource(streamUrl);
        eventSources.set(doc.id, eventSource);

        eventSource.onopen = () => {
          console.log(`✅ SSE auto-connected for document ${doc.id}`);
        };

        eventSource.addEventListener('progress', (event) => {
          console.log(`📊 Progress event (auto) for doc ${doc.id}:`, event.data);
          const progressData = JSON.parse(event.data);

          // Translate message to Polish
          if (progressData.message) {
            progressData.message = translateProgressMessage(progressData.message, progressData.step);
          }

          // Translate step name
          if (progressData.step) {
            const stepKey = `documents.progress.steps.${progressData.step}`;
            const translatedStep = t(stepKey);
            if (translatedStep !== stepKey) {
              progressData.step = translatedStep;
            }
          }

          console.log(`🔑 Setting documentProgress[${doc.id}] (type: ${typeof doc.id})`);
          setDocumentProgress(prev => {
            const updated = {
              ...prev,
              [doc.id]: progressData
            };
            console.log('📦 Updated documentProgress:', updated);
            return updated;
          });

          if (progressData.status === 'completed' || progressData.status === 'failed') {
            console.log(`🏁 Processing complete (auto) for doc ${doc.id}:`, progressData.status);
            eventSource.close();
            eventSources.delete(doc.id);
            loadDocuments();
          }
        });

        eventSource.addEventListener('close', () => {
          console.log(`🔒 SSE connection closed (auto) for doc ${doc.id}`);
          eventSource.close();
          eventSources.delete(doc.id);
        });

        eventSource.onerror = (error) => {
          console.error(`❌ EventSource error (auto) for doc ${doc.id}:`, error);
          eventSource.close();
          eventSources.delete(doc.id);
        };
      }
    });

    // Cleanup: close all EventSource connections on unmount
    return () => {
      console.log('🧹 Cleaning up auto-connected EventSources');
      eventSources.forEach((eventSource, docId) => {
        console.log(`🔌 Closing EventSource for doc ${docId}`);
        eventSource.close();
      });
      eventSources.clear();
    };
  }, [documents]);

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const response = await projectsApi.list();
      const projectsData = response.data.projects || response.data || [];
      setProjects(projectsData);

      // Auto-select first project if available
      if (projectsData.length > 0 && !selectedProjectId) {
        setSelectedProjectId(projectsData[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('projects.errors.loadFailed'));
    } finally {
      setLoadingProjects(false);
    }
  };

  // Translate backend progress messages to Polish
  const translateProgressMessage = (message: string, step: string): string => {
    // Embeddings generation: "Generated X/Y embeddings (Z%)"
    const embeddingsMatch = message.match(/Generated (\d+)\/(\d+) embeddings \((\d+)%\)/);
    if (embeddingsMatch) {
      return `Przygotowywanie do wyszukiwania ${embeddingsMatch[1]}/${embeddingsMatch[2]} (${embeddingsMatch[3]}%)`;
    }

    // Chunking: "Created X text chunks"
    const chunksMatch = message.match(/Created (\d+) text chunks/);
    if (chunksMatch) {
      return `Podzielono na ${chunksMatch[1]} fragmentów`;
    }

    // Extraction: "Extracted text from X pages" or "Text extraction complete"
    if (message.includes('extraction complete') || message.includes('Extracted text')) {
      const pagesMatch = message.match(/(\d+) pages/);
      if (pagesMatch) {
        return `Wyodrębniono tekst z ${pagesMatch[1]} stron`;
      }
      return 'Wyodrębnianie tekstu zakończone';
    }

    // Storage: "Storing X chunks" or similar
    const storingMatch = message.match(/Storing (\d+) chunks/);
    if (storingMatch) {
      return `Zapisywanie ${storingMatch[1]} fragmentów`;
    }

    // Storage complete: "Successfully processed X pages into Y chunks"
    const successMatch = message.match(/Successfully processed (\d+) pages into (\d+) chunks/);
    if (successMatch) {
      return `Pomyślnie przetworzono ${successMatch[1]} stron na ${successMatch[2]} fragmentów`;
    }

    // Fallback: use original message
    return message;
  };

  const loadDocuments = async () => {
    if (!selectedProjectId) return;

    try {
      setLoadingDocuments(true);
      setError('');
      const response = await documentsApi.list(selectedProjectId);
      const documentsData = response.data.documents || response.data || [];
      setDocuments(documentsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('documents.errors.loadFailed'));
    } finally {
      setLoadingDocuments(false);
    }
  };

  // File upload with drag & drop
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!selectedProjectId) {
      setError(t('documents.noProjectSelected'));
      return;
    }

    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file type
    if (file.type !== 'application/pdf') {
      setError(t('documents.upload.invalidFile'));
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(t('documents.upload.fileTooLarge'));
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setError('');

      // Upload file (API handles FormData creation internally)
      await documentsApi.upload(file, selectedProjectId);

      setUploadProgress(100);

      // Reload documents
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('documents.upload.error'));
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  }, [selectedProjectId, t]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: uploading || !selectedProjectId
  });

  // Process document with real-time progress streaming
  const handleProcess = async (documentId: number) => {
    try {
      setProcessingDocId(documentId);
      setError('');
      
      // Initialize progress
      setDocumentProgress(prev => ({
        ...prev,
        [documentId]: {
          percentage: 0,
          step: 'starting',
          message: t('documents.progress.starting'),
          status: 'processing'
        }
      }));
      
      // Start processing
      await documentsApi.process(documentId);
      
      // Establish EventSource connection for real-time progress
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8765';
      const token = localStorage.getItem('access_token');
      const streamUrl = `${API_BASE_URL}/api/v1/documents/${documentId}/progress/stream?token=${token}`;
      console.log('🔗 Connecting to SSE stream:', streamUrl);

      const eventSource = new EventSource(streamUrl);

      eventSource.onopen = () => {
        console.log('✅ SSE connection opened');
      };

      // Listen for 'progress' events from SSE
      eventSource.addEventListener('progress', (event) => {
        console.log('📊 Progress event received:', event.data);
        const progressData = JSON.parse(event.data);

        // Translate message to Polish
        if (progressData.message) {
          progressData.message = translateProgressMessage(progressData.message, progressData.step);
        }

        // Translate step name
        if (progressData.step) {
          const stepKey = `documents.progress.steps.${progressData.step}`;
          const translatedStep = t(stepKey);
          if (translatedStep !== stepKey) {
            progressData.step = translatedStep;
          }
        }

        console.log(`🔑 Setting documentProgress[${documentId}] (type: ${typeof documentId})`);
        setDocumentProgress(prev => {
          const updated = {
            ...prev,
            [documentId]: progressData
          };
          console.log('📦 Updated documentProgress:', updated);
          return updated;
        });

        // Check if completed or failed
        if (progressData.status === 'completed' || progressData.status === 'failed') {
          console.log('🏁 Processing complete:', progressData.status);
          eventSource.close();
          setProcessingDocId(null);
          // Reload documents to get final status
          loadDocuments();
        }
      });

      eventSource.addEventListener('close', () => {
        console.log('🔒 SSE connection closed by server');
        eventSource.close();
        setProcessingDocId(null);
      });

      eventSource.onerror = (error) => {
        console.error('❌ EventSource error:', error);
        console.log('EventSource readyState:', eventSource.readyState);
        eventSource.close();
        setProcessingDocId(null);
        loadDocuments();
      };
      
    } catch (err) {
      setError(err instanceof Error ? err.message : t('documents.process.error'));
      setProcessingDocId(null);
    }
  };

  // Open delete dialog
  const openDeleteDialog = (document: Document) => {
    setDeleteDocument(document);
    setDeleteOpen(true);
  };

  // Delete document
  const handleDelete = async () => {
    if (!deleteDocument) return;

    try {
      setDeleteLoading(true);
      await documentsApi.delete(deleteDocument.id);
      setDeleteOpen(false);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('documents.delete.error'));
    } finally {
      setDeleteLoading(false);
    }
  };

  // Generate category tree from ToC
  const handleGenerateTree = async (documentId: number) => {
    try {
      setGeneratingTreeDocId(documentId);
      setError('');

      const response = await documentsApi.generateTree(documentId, {
        auto_assign_document: true,
        validate_depth: true,
      });

      // Redirect to Document Explorer instead of showing popup
      navigate(`/documents/${documentId}/explorer`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('documents.generateTree.error', 'Failed to generate category tree'));
    } finally {
      setGeneratingTreeDocId(null);
    }
  };

  // Export document as Markdown
  const handleExportDocument = async (documentId: number, filename: string) => {
    try {
      const response = await exportApi.exportDocumentMarkdown(documentId);
      const cleanFilename = filename.replace('.pdf', '');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const exportFilename = `${cleanFilename}_${timestamp}.md`;
      downloadBlob(response.data, exportFilename);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('documents.errors.exportFailed'));
    }
  };

  // Get status badge
  const getStatusBadge = (status: ProcessingStatus) => {
    switch (status) {
      case 'pending':
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            {t('documents.status.pending')}
          </Badge>
        );
      case 'processing':
        return (
          <Badge className="gap-1 bg-primary-600">
            <Loader2 className="h-3 w-3 animate-spin" />
            {t('documents.status.processing')}
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="default" className="gap-1 bg-success-600">
            <CheckCircle2 className="h-3 w-3" />
            {t('documents.status.completed')}
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            {t('documents.status.failed')}
          </Badge>
        );
    }
  };

  // Format file size
  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pl-PL', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const selectedProject = projects.find(p => p.id === selectedProjectId);

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
      {/* Header */}
      <header className="border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/projects')}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                {t('documents.backToProjects')}
              </Button>
              <div className="h-8 w-px bg-neutral-200 dark:bg-neutral-800" />
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
                {t('app.name')}
              </h1>
            </div>
            <div className="flex items-center gap-4">
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Header with Project Selector */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-neutral-900 dark:text-neutral-50">
                {t('documents.title')}
              </h2>
              <p className="text-neutral-600 dark:text-neutral-400 mt-2">
                {selectedProject?.name || t('documents.description')}
              </p>
            </div>

            {/* Project Selector */}
            <div className="w-64">
              <Select
                value={selectedProjectId ? selectedProjectId.toString() : ""}
                onValueChange={(value: string) => setSelectedProjectId(parseInt(value))}
                disabled={loadingProjects}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('documents.selectProject')} />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.id} value={project.id.toString()}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded text-error-700 dark:text-error-400">
              {error}
            </div>
          )}

          {/* No Project Selected */}
          {!selectedProjectId && !loadingProjects && (
            <Card className="text-center py-12">
              <CardContent>
                <FileText className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
                  {t('documents.noProjectSelected')}
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                  {t('documents.noProjectSelectedDescription')}
                </p>
                <Button onClick={() => navigate('/projects')}>
                  {t('documents.backToProjects')}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Upload Area */}
          {selectedProjectId && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  {t('documents.upload.title')}
                </CardTitle>
                <CardDescription>{t('documents.upload.description')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div
                  {...getRootProps()}
                  className={`
                    border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                    transition-colors
                    ${isDragActive
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-neutral-300 dark:border-neutral-700 hover:border-primary-400 dark:hover:border-primary-600'
                    }
                    ${(!selectedProjectId || uploading) ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <input {...getInputProps()} />
                  <Upload className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                  {uploading ? (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                        {t('documents.upload.uploading')}
                      </p>
                      <div className="w-full max-w-xs mx-auto bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">
                        {uploadProgress}%
                      </p>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50 mb-2">
                        {isDragActive
                          ? t('documents.upload.dropzoneActive')
                          : t('documents.upload.dropzone')
                        }
                      </p>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">
                        {t('documents.upload.maxSize')} • {t('documents.upload.acceptedFormats')}
                      </p>
                    </>
                  )}
                </div>

                {/* Agentic Crawl Option */}
                <div className="flex items-center gap-4 pt-4 border-t">
                  <div className="flex-1 text-sm text-neutral-600 dark:text-neutral-400">
                    {t('documents.agenticCrawl.alternative', 'Lub użyj AI do ekstrakcji z internetu')}
                  </div>
                  <AgenticCrawlDialog
                    projectId={selectedProjectId}
                    onSuccess={() => loadDocuments()}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Loading Documents */}
          {loadingDocuments && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            </div>
          )}

          {/* Empty State */}
          {!loadingDocuments && selectedProjectId && documents.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <FileText className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50 mb-2">
                  {t('documents.noDocuments')}
                </h3>
                <p className="text-neutral-600 dark:text-neutral-400">
                  {t('documents.noDocumentsDescription')}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Documents List */}
          {!loadingDocuments && selectedProjectId && documents.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {documents.map((doc) => (
                <Card key={doc.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg line-clamp-2">
                        {doc.filename}
                      </CardTitle>
                      {getStatusBadge(doc.processing_status)}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {/* Progress Bar for Processing Documents */}
                    {(() => {
                      const isProcessing = doc.processing_status?.toLowerCase() === 'processing';
                      const hasProgress = documentProgress[doc.id];
                      console.log(`🎨 Render check for doc ${doc.id} (type: ${typeof doc.id}):`, {
                        isProcessing,
                        hasProgress,
                        progressData: hasProgress ? documentProgress[doc.id] : 'none',
                        allProgressKeys: Object.keys(documentProgress)
                      });
                      return isProcessing && hasProgress;
                    })() && (
                      <div className="mb-4 p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-primary-700 dark:text-primary-300">
                            {documentProgress[doc.id].message}
                          </span>
                          <span className="text-primary-600 dark:text-primary-400 font-semibold">
                            {documentProgress[doc.id].percentage}%
                          </span>
                        </div>
                        <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2.5">
                          <div
                            className="bg-primary-600 h-2.5 rounded-full transition-all duration-300 ease-in-out"
                            style={{ width: `${documentProgress[doc.id].percentage}%` }}
                          />
                        </div>
                        <p className="text-xs text-primary-600 dark:text-primary-400">
                          {t('documents.progress.step')}: {documentProgress[doc.id].step}
                        </p>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600 dark:text-neutral-400">
                        {t('documents.stats.pages')}
                      </span>
                      <span className="font-medium text-neutral-900 dark:text-neutral-50">
                        {doc.page_count || '-'}
                      </span>
                    </div>
                    {/* Chunks info - not available in current Document type */}
                    {/*
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600 dark:text-neutral-400">
                        {t('documents.stats.chunks')}
                      </span>
                      <span className="font-medium text-neutral-900 dark:text-neutral-50">
                        -
                      </span>
                    </div>
                    */}
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-neutral-600 dark:text-neutral-400">
                        {t('documents.stats.fileSize')}
                      </span>
                      <span className="font-medium text-neutral-900 dark:text-neutral-50">
                        {formatFileSize(doc.file_size)}
                      </span>
                    </div>
                    <div className="pt-2 border-t border-neutral-200 dark:border-neutral-800">
                      <p className="text-xs text-neutral-500 dark:text-neutral-600">
                        {t('documents.stats.uploadedAt')}: {formatDate(doc.created_at)}
                      </p>
                    </div>
                  </CardContent>
                  <CardFooter className="flex flex-col gap-2">
                    {/* Primary Actions Row */}
                    {doc.processing_status === 'pending' && (
                      <div className="flex gap-2 w-full">
                        <Button
                          size="sm"
                          onClick={() => handleProcess(doc.id)}
                          disabled={processingDocId === doc.id}
                          className="flex-1"
                        >
                          {processingDocId === doc.id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              {t('documents.process.processing')}
                            </>
                          ) : (
                            <>
                              <Play className="mr-2 h-4 w-4" />
                              {t('documents.actions.process')}
                            </>
                          )}
                        </Button>
                      </div>
                    )}
                    {doc.processing_status === 'completed' && (
                      <div className="flex gap-2 w-full">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleGenerateTree(doc.id)}
                          disabled={generatingTreeDocId === doc.id}
                          className="flex-1"
                        >
                          {generatingTreeDocId === doc.id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              {t('documents.generateTree.generating', 'Generating...')}
                            </>
                          ) : (
                            <>
                              <FolderTree className="mr-2 h-4 w-4" />
                              {t('documents.actions.generateTree', 'Generate Categories')}
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleProcess(doc.id)}
                          disabled={processingDocId === doc.id}
                          className="flex-1"
                        >
                          {processingDocId === doc.id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              {t('documents.process.processing')}
                            </>
                          ) : (
                            <>
                              <Play className="mr-2 h-4 w-4" />
                              {t('documents.actions.reprocess')}
                            </>
                          )}
                        </Button>
                      </div>
                    )}
                    {/* Secondary Actions Row - Always visible */}
                    <div className="flex gap-2 w-full">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExportDocument(doc.id, doc.filename)}
                        title={t('common.export', 'Export as Markdown')}
                        className="flex-1"
                      >
                        <Download className="mr-2 h-4 w-4" />
                        {t('documents.actions.download', 'Download')}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDeleteDialog(doc)}
                        className="flex-1"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        {t('documents.actions.delete', 'Delete')}
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Delete Document Dialog */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('documents.delete.title')}</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2">
                <div>{t('documents.delete.description')}</div>
                {deleteDocument && (
                  <div className="font-medium text-neutral-900 dark:text-neutral-50">
                    {deleteDocument.filename}
                  </div>
                )}
                <div className="text-error-600 dark:text-error-400">
                  {t('documents.delete.warning')}
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteLoading}>
              {t('documents.delete.cancel')}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className="bg-error-600 hover:bg-error-700 dark:bg-error-700 dark:hover:bg-error-800"
            >
              {deleteLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {deleteLoading ? t('documents.delete.deleting') : t('documents.delete.confirm')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
