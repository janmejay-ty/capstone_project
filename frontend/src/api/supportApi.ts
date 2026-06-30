import api from './client';

export interface SafetyCheck {
  passed: boolean;
  details: string;
}

export interface MessageState {
  current_agent: string;
  plan_steps: string[];
  sql_results: Record<string, any>;
  safety_check: SafetyCheck;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  state?: MessageState;
}

export interface ChatResponse {
  response: string;
  state: MessageState;
}

export interface HistoryResponse {
  history: Message[];
}

export const supportApi = {
  chat: async (message: string, sessionId: string): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },

  sendFeedback: async (
    sessionId: string,
    messageIndex: number,
    feedbackType: 'up' | 'down'
  ): Promise<{ status: string; message: string }> => {
    const response = await api.post<{ status: string; message: string }>('/feedback', {
      session_id: sessionId,
      message_index: messageIndex,
      feedback_type: feedbackType,
    });
    return response.data;
  },

  getHistory: async (sessionId: string): Promise<HistoryResponse> => {
    const response = await api.get<HistoryResponse>(`/history/${sessionId}`);
    return response.data;
  },

  clearSession: async (sessionId: string): Promise<{ status: string; message: string }> => {
    const response = await api.post<{ status: string; message: string }>(`/clear/${sessionId}`);
    return response.data;
  },
};
