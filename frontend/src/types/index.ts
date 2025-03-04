export interface Message {
  content: string
  isUser: boolean
  timestamp: Date
}

export interface ChatResponse {
  response: string
}

export interface UserInfo {
  name: string;
  email: string;
  companyName: string;
  companyType: string;
  purpose: string;
  jobRole: string;
  sessionId?: string;
}

export type FormStatus = 'not_submitted' | 'submitted'; 