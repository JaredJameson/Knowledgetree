/**
 * KnowledgeTree API Types
 * TypeScript interfaces for API requests and responses
 */

// Auth types
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

// Project types
export interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  created_at: string;
  updated_at: string;
  document_count: number;
  total_chunks: number;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

// Document types
export const DocumentType = {
  PDF: 'pdf',
  WEB: 'web',
  TEXT: 'text',
} as const;

export type DocumentType = typeof DocumentType[keyof typeof DocumentType];

export const ProcessingStatus = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export type ProcessingStatus = typeof ProcessingStatus[keyof typeof ProcessingStatus];

export interface Document {
  id: number;
  filename: string;
  title: string | null;
  source_type: DocumentType;
  source_url: string | null;
  file_path: string | null;
  file_size: number | null;
  page_count: number | null;
  processing_status: ProcessingStatus;
  error_message: string | null;
  category_id: number | null;
  project_id: number;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentUploadResponse {
  id: number;
  filename: string;
  file_size: number;
  processing_status: ProcessingStatus;
  message: string;
}

// Search types
export interface SearchResult {
  chunk_id: number;
  document_id: number;
  document_title: string | null;
  document_filename: string;
  chunk_text: string;
  chunk_index: number;
  similarity_score: number;
  chunk_metadata: Record<string, any> | null;
  document_created_at: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  execution_time_ms: number;
  filters_applied: {
    project_id: number;
    category_id: number | null;
    min_similarity: number;
    limit: number;
  };
}

export interface SearchStatistics {
  total_documents: number;
  total_chunks: number;
  embedded_chunks: number;
  average_chunk_length: number;
  total_storage_mb: number;
}

// Chat types
export const MessageRole = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
} as const;

export type MessageRole = typeof MessageRole[keyof typeof MessageRole];

export interface Message {
  id: number;
  role: MessageRole;
  content: string;
  created_at: string;
  tokens_used: number | null;
}

export interface RetrievedChunk {
  chunk_id: number;
  document_id: number;
  document_title: string | null;
  document_filename: string;
  chunk_text: string;
  similarity_score: number;
}

export interface ChatResponse {
  conversation_id: number;
  message: Message;
  retrieved_chunks: RetrievedChunk[];
  tokens_used: number;
  model: string;
  processing_time_ms: number;
  artifact_id?: number;
}

export interface Conversation {
  id: number;
  title: string | null;
  project_id: number;
  created_at: string;
  updated_at: string;
  message_count: number;
  total_tokens_used: number;
}

export interface ConversationWithMessages {
  id: number;
  title: string | null;
  project_id: number;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  page: number;
  page_size: number;
}

// Category types
export interface Category {
  id: number;
  name: string;
  description: string | null;
  color: string;
  icon: string;
  depth: number;
  order: number;
  page_start: number | null;
  page_end: number | null;
  parent_id: number | null;
  project_id: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryTreeNode extends Category {
  children: CategoryTreeNode[];
}

export interface CategoryListResponse {
  categories: Category[];
  total: number;
  page: number;
  page_size: number;
}

export interface CategoryCreateRequest {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  depth?: number;
  order?: number;
  parent_id?: number | null;
}

export interface CategoryUpdateRequest {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  order?: number;
  parent_id?: number | null;
}

export interface GenerateTreeRequest {
  parent_id?: number | null;
  validate_depth?: boolean;
  auto_assign_document?: boolean;
}

export interface GenerateTreeResponse {
  success: boolean;
  message: string;
  categories: Category[];
  stats: {
    total_entries: number;
    total_created: number;
    skipped_depth?: number;
    max_depth: number;
  };
}
