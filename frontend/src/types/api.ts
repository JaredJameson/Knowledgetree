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

// Analytics types
export interface DailyMetric {
  date: string;
  documents_uploaded: number;
  searches_performed: number;
  chat_messages_sent: number;
  insights_generated: number;
  active_users: number;
}

export interface MetricsResponse {
  project_id: number;
  period_days: number;
  metrics: DailyMetric[];
  total_documents: number;
  total_searches: number;
  total_messages: number;
  total_insights: number;
}

export interface ActivityEvent {
  id: number;
  user_id: number;
  event_type: string;
  event_data: Record<string, any>;
  created_at: string;
}

export interface ActivityFeedResponse {
  project_id: number;
  activities: ActivityEvent[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface QualityScoreResponse {
  project_id: number;
  overall_score: number;
  document_score: number;
  search_score: number;
  chat_score: number;
  diversity_score: number;
  period_days: number;
  metrics: {
    total_documents: number;
    total_searches: number;
    total_messages: number;
    document_count: number;
  };
}

export interface TrendDataPoint {
  current: number;
  previous: number;
  change_percent: number;
}

export interface TrendsResponse {
  project_id: number;
  period_days: number;
  documents_uploaded: TrendDataPoint;
  searches_performed: TrendDataPoint;
  chat_messages_sent: TrendDataPoint;
  insights_generated: TrendDataPoint;
}

// Knowledge Graph types
export interface CentralityMetrics {
  degree: number;
  betweenness: number;
  closeness: number;
  eigenvector: number;
}

export interface GraphNode {
  id: number;
  name: string;
  type: string;
  occurrence_count: number;
  community?: number;
  centrality?: CentralityMetrics;
  clustering?: number;
}

export interface GraphEdge {
  source: number;
  target: number;
  weight: number;
  co_occurrence_count: number;
}

export interface GraphStatistics {
  nodes: number;
  edges: number;
  density: number;
  components: number;
  avg_degree: number;
  avg_clustering: number;
  diameter?: number;
  radius?: number;
  largest_component_size?: number;
}

export interface KnowledgeGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  statistics: GraphStatistics;
}

export interface BuildGraphRequest {
  min_strength?: number;
  include_isolated?: boolean;
  include_communities?: boolean;
  include_centrality?: boolean;
  include_clustering?: boolean;
}

export interface EntityListItem {
  id: number;
  name: string;
  type: string;
  occurrence_count: number;
}

export interface EntityListResponse {
  total: number;
  entities: EntityListItem[];
}

export interface RelationshipListItem {
  id: number;
  source_id: number;
  source_name: string;
  target_id: number;
  target_name: string;
  strength: number;
  co_occurrence_count: number;
}

export interface RelationshipListResponse {
  total: number;
  relationships: RelationshipListItem[];
}

export interface EntityNeighbor {
  id: number;
  name: string;
  distance: number;
  path_weight: number;
}

export interface EntityDetailsResponse {
  id: number;
  name: string;
  type: string;
  occurrence_count: number;
  community?: number;
  centrality?: CentralityMetrics;
  clustering?: number;
  neighbors: EntityNeighbor[];
}

export interface PathNode {
  id: number;
  name: string;
}

export interface PathResponse {
  exists: boolean;
  length?: number;
  path?: PathNode[];
  total_weight?: number;
}

export interface FindPathRequest {
  source_entity_id: number;
  target_entity_id: number;
  weighted?: boolean;
}

export interface Community {
  id: number;
  size: number;
  entities: number[];
}

export interface CommunitiesResponse {
  num_communities: number;
  communities: Community[];
  modularity: number;
}
