/**
 * KnowledgeTree Content Workbench Types
 * TypeScript interfaces for Content Editor, Versioning, AI Operations, and Templates
 */

// Content Status Enum
export const ContentStatus = {
  DRAFT: 'draft',
  REVIEW: 'review',
  PUBLISHED: 'published',
} as const;

export type ContentStatus = typeof ContentStatus[keyof typeof ContentStatus];

// Tone Types for AI Rewriting
export const ToneType = {
  PROFESSIONAL: 'professional',
  CASUAL: 'casual',
  TECHNICAL: 'technical',
  FRIENDLY: 'friendly',
  FORMAL: 'formal',
  CONVERSATIONAL: 'conversational',
} as const;

export type ToneType = typeof ToneType[keyof typeof ToneType];

// Reading Levels for Simplification
export const ReadingLevel = {
  BASIC: 'basic',
  INTERMEDIATE: 'intermediate',
  ADVANCED: 'advanced',
} as const;

export type ReadingLevel = typeof ReadingLevel[keyof typeof ReadingLevel];

// Quote Types
export const QuoteType = {
  FACT: 'fact',
  OPINION: 'opinion',
  DEFINITION: 'definition',
  STATISTIC: 'statistic',
  EXAMPLE: 'example',
} as const;

export type QuoteType = typeof QuoteType[keyof typeof QuoteType];

// Template Types
export const TemplateType = {
  HOW_TO: 'how_to',
  FAQ: 'faq',
  TUTORIAL: 'tutorial',
  ARTICLE: 'article',
  REFERENCE: 'reference',
} as const;

export type TemplateType = typeof TemplateType[keyof typeof TemplateType];

// Extended Category with Content Workbench fields
export interface CategoryWithContent {
  id: number;
  name: string;
  description: string | null;
  color: string;
  icon: string;
  depth: number;
  order: number;
  parent_id: number | null;
  project_id: number;
  merged_content: string | null;

  // Content Workbench fields
  draft_content: string | null;
  published_content: string | null;
  content_status: ContentStatus;
  published_at: string | null;
  reviewed_by: number | null;
  reviewed_at: string | null;

  created_at: string;
  updated_at: string;
}

// Content Version
export interface ContentVersion {
  id: number;
  category_id: number;
  version_number: number;
  content: string;
  created_by: number | null;
  created_at: string;
  change_summary: string | null;
}

// Extracted Quote
export interface ExtractedQuote {
  id: number;
  category_id: number;
  quote_text: string;
  context_before: string | null;
  context_after: string | null;
  quote_type: QuoteType | null;
  created_at: string;
}

// Content Template
export interface ContentTemplate {
  id: number;
  name: string;
  description: string | null;
  template_type: TemplateType;
  structure: {
    sections: TemplateSection[];
  };
  is_public: boolean;
  created_by: number | null;
  created_at: string;
}

export interface TemplateSection {
  title: string;
  prompt: string;
  order: number;
}

// Request Types

export interface SaveDraftRequest {
  draft_content: string;
  change_summary?: string;
  auto_version?: boolean;
}

export interface PublishContentRequest {
  create_version?: boolean;
}

export interface RestoreVersionRequest {
  version_number: number;
  create_new_version?: boolean;
}

export interface CompareVersionsRequest {
  version_a: number;
  version_b: number;
}

export interface SummarizeRequest {
  content: string;
  max_length?: number;
  focus?: string;
}

export interface ExpandRequest {
  content: string;
  target_length?: number;
  add_details?: string;
}

export interface SimplifyRequest {
  content: string;
  reading_level?: ReadingLevel;
}

export interface RewriteToneRequest {
  content: string;
  tone: ToneType;
  preserve_facts?: boolean;
}

export interface ExtractQuotesRequest {
  content: string;
  max_quotes?: number;
  quote_types?: QuoteType[];
}

export interface GenerateOutlineRequest {
  topic: string;
  depth?: number;
  style?: TemplateType;
}

export interface ContentTemplateCreateRequest {
  name: string;
  description?: string;
  template_type: TemplateType;
  sections: TemplateSectionCreate[];
  is_public?: boolean;
}

export interface TemplateSectionCreate {
  title: string;
  prompt: string;
  order: number;
}

// Response Types

export interface VersionComparisonResponse {
  version_a: {
    number: number;
    content: string;
    created_at: string;
    created_by: number | null;
    change_summary: string | null;
  };
  version_b: {
    number: number;
    content: string;
    created_at: string;
    created_by: number | null;
    change_summary: string | null;
  };
}

export interface AIOperationResponse {
  result: string;
  operation: string;
  tokens_used: number | null;
}
