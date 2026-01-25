/**
 * Artifact type definitions
 * Matches backend ArtifactType enum and schemas
 */

export type ArtifactType =
  | 'summary'
  | 'article'
  | 'extract'
  | 'notes'
  | 'outline'
  | 'comparison'
  | 'explanation'
  | 'category_tree'
  | 'custom';

export interface ArtifactMetadata {
  model?: string;
  temperature?: number;
  max_tokens?: number;
  tokens_used?: number;
  input_tokens?: number;
  output_tokens?: number;
  processing_time_ms?: number;
  chunks_retrieved?: number;
  source_documents?: string[];
  query?: string;
  category_id?: number;
  instructions?: string;
  [key: string]: any; // Allow additional custom metadata
}

export interface Artifact {
  id: number;
  type: ArtifactType;
  title: string;
  content: string;
  version: number;
  project_id: number;
  user_id: number;
  conversation_id: number | null;
  category_id: number | null;
  metadata: ArtifactMetadata | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactListItem {
  id: number;
  type: ArtifactType;
  title: string;
  version: number;
  conversation_id: number | null;
  category_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ArtifactListResponse {
  artifacts: ArtifactListItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ArtifactCreateRequest {
  type: ArtifactType;
  title: string;
  content: string;
  conversation_id?: number;
  category_id?: number;
  metadata?: ArtifactMetadata;
}

export interface ArtifactUpdateRequest {
  title?: string;
  content?: string;
  type?: ArtifactType;
  conversation_id?: number;
  category_id?: number;
  metadata?: ArtifactMetadata;
}

export interface ArtifactRegenerateRequest {
  metadata?: ArtifactMetadata;
}

export interface ArtifactGenerateRequest {
  artifact_type: ArtifactType;
  title: string;
  query: string;
  category_id?: number;
  conversation_id?: number;
  instructions?: string;
  temperature?: number;
  max_tokens?: number;
}

// Type guards
export function isArtifactType(value: string): value is ArtifactType {
  return [
    'summary',
    'article',
    'extract',
    'notes',
    'outline',
    'comparison',
    'explanation',
    'category_tree',
    'custom',
  ].includes(value);
}

// Display helpers
export const ARTIFACT_TYPE_LABELS: Record<ArtifactType, string> = {
  summary: 'Summary',
  article: 'Article',
  extract: 'Extract',
  notes: 'Notes',
  outline: 'Outline',
  comparison: 'Comparison',
  explanation: 'Explanation',
  category_tree: 'Knowledge Tree',
  custom: 'Custom',
};

export const ARTIFACT_TYPE_DESCRIPTIONS: Record<ArtifactType, string> = {
  summary: 'Concise summary of key points and main ideas',
  article: 'Comprehensive article with introduction, body, and conclusion',
  extract: 'Extracted key information, facts, and data',
  notes: 'Study notes organized for review and learning',
  outline: 'Hierarchical structure of topics and subtopics',
  comparison: 'Side-by-side comparison of concepts or topics',
  explanation: 'Clear explanation of complex concepts',
  category_tree: 'Interactive hierarchical category tree from content - edit, expand, and organize knowledge',
  custom: 'Custom content based on specific instructions',
};

export const ARTIFACT_TYPE_ICONS: Record<ArtifactType, string> = {
  summary: 'FileText',
  article: 'FileEdit',
  extract: 'Clipboard',
  notes: 'StickyNote',
  outline: 'List',
  comparison: 'ArrowLeftRight',
  explanation: 'Lightbulb',
  category_tree: 'FolderTree',
  custom: 'Sparkles',
};
