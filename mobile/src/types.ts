export type MessageRecord = {
  role: string;
  content: string;
};

export type ModeOption = {
  name: string;
  instruction: string;
};

export type AgendaItem = {
  id: string;
  title: string;
  source: string;
  time_reference: string | null;
  status: string;
  priority: string;
  created_at?: string | null;
  updated_at?: string | null;
};

export type HealthState = {
  ok: boolean;
  report: string;
};

export type ModeResponse = {
  mode: string;
  modes: ModeOption[];
};

export type AgendaResponse = {
  items: AgendaItem[];
};

export type RemindersResponse = {
  items: AgendaItem[];
  due_messages: string[];
};

export type HistoryResponse = {
  items: MessageRecord[];
};

export type ChatResponse = {
  reply: string;
  mode: string;
  reminders: string[];
  captured_commitment?: AgendaItem | null;
};
