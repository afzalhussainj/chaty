export type SourceType = 'html_page' | 'pdf';

export interface Citation {
  title: string;
  url: string;
  source_type: SourceType;
  page_number: number | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  isLoading?: boolean;
  isError?: boolean;
  noResult?: boolean;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  confidence?: 'high' | 'medium' | 'low';
  noResult?: boolean;
}