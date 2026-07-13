import { useState, useEffect, useRef } from 'react'
import { 
  Send, 
  Trash2, 
  ThumbsUp, 
  ThumbsDown, 
  Bot, 
  User, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Database, 
  ListChecks, 
  ShieldCheck, 
  Sparkles,
  Terminal,
  Clock,
  Sun,
  Moon
} from 'lucide-react'
import { supportApi } from './api/supportApi'
import type { Message } from './api/supportApi'
import MarkdownRenderer from './components/MarkdownRenderer'

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeState, setActiveState] = useState({
    current_agent: 'Idle',
    plan_steps: [] as string[],
    sql_results: {} as Record<string, any>,
    safety_check: { passed: true, details: 'System Ready' }
  });
  const [feedbackLog, setFeedbackLog] = useState<Record<number, 'up' | 'down'>>({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('resolvedesk_theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return 'dark';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'light') {
      root.classList.add('light');
    } else {
      root.classList.remove('light');
    }
    localStorage.setItem('resolvedesk_theme', theme);
  }, [theme]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize or load session ID
  useEffect(() => {
    let savedSessionId = sessionStorage.getItem('resolvedesk_session_id');
    if (!savedSessionId) {
      savedSessionId = 'session_' + Math.random().toString(36).substring(2, 15);
      sessionStorage.setItem('resolvedesk_session_id', savedSessionId);
    }
    setSessionId(savedSessionId);
    fetchHistory(savedSessionId);
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchHistory = async (session: string) => {
    try {
      const data = await supportApi.getHistory(session);
      setMessages(data.history || []);
      if (data.history && data.history.length > 0) {
        // Sync with the state of the last assistant message
        const assistantMsgs = data.history.filter((m: Message) => m.role === 'assistant');
        if (assistantMsgs.length > 0) {
          const lastMsg = assistantMsgs[assistantMsgs.length - 1];
          if (lastMsg.state) {
            setActiveState(lastMsg.state);
          }
        }
      }
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessageContent = input;
    setInput('');
    setLoading(true);

    // Optimistically add user message
    const userMessage: Message = {
      role: 'user',
      content: userMessageContent,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const data = await supportApi.chat(userMessageContent, sessionId);
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        state: data.state
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      if (data.state) {
        setActiveState(data.state);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        role: 'assistant',
        content: "Sorry, I am unable to connect to the backend server. Please verify that the FastAPI backend is running.",
        timestamp: new Date().toISOString(),
        state: {
          current_agent: 'System Error',
          plan_steps: [],
          sql_results: { error: 'Failed to connect to backend api' },
          safety_check: { passed: false, details: 'Network connection failure' }
        }
      };
      setMessages(prev => [...prev, errorMessage]);
      setActiveState(errorMessage.state!);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (msgIndex: number, type: 'up' | 'down') => {
    setFeedbackLog(prev => ({ ...prev, [msgIndex]: type }));
    try {
      await supportApi.sendFeedback(sessionId, msgIndex, type);
    } catch (error) {
      console.error("Error sending feedback:", error);
    }
  };

  const handleClear = async () => {
    if (!window.confirm("Are you sure you want to clear this session's history?")) return;
    try {
      await supportApi.clearSession(sessionId);
      setMessages([]);
      setFeedbackLog({});
      setActiveState({
        current_agent: 'Idle',
        plan_steps: [],
        sql_results: {},
        safety_check: { passed: true, details: 'Session Cleared' }
      });
    } catch (error) {
      console.error("Error clearing session:", error);
    }
  };

  const regenerateSession = () => {
    const newSession = 'session_' + Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem('resolvedesk_session_id', newSession);
    setSessionId(newSession);
    setMessages([]);
    setFeedbackLog({});
    setActiveState({
      current_agent: 'Idle',
      plan_steps: [],
      sql_results: {},
      safety_check: { passed: true, details: 'New Session Started' }
    });
  };

  return (
    <div className="flex flex-col h-screen bg-main-bg text-main-text transition-colors duration-200">
      {/* Navbar Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-panel-bg border-b border-main-border shadow-lg transition-colors duration-200">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-600/25 border border-purple-500/50 rounded-xl text-purple-400">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-main-text flex items-center gap-2">
              ResolveDesk AI <span className="text-xs px-2 py-0.5 rounded-full bg-purple-600/30 text-purple-300 font-normal">Co-Pilot</span>
            </h1>
            <p className="text-xs text-muted-text">Multi-Agent Support Resolution Network</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-muted-text uppercase tracking-wider">Session Identifier</p>
            <p className="font-mono text-xs text-purple-400 dark:text-purple-300 font-semibold">{sessionId}</p>
          </div>
          <button 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            className="p-2 hover:bg-hover-bg rounded-lg border border-main-border hover:border-purple-500/50 transition-all text-muted-text hover:text-main-text"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title={sidebarOpen ? "Collapse Trace Panel" : "Expand Trace Panel"}
            className={`p-2 rounded-lg border border-main-border transition-all hover:border-purple-500/50 hover:bg-hover-bg ${
              sidebarOpen ? 'text-purple-400 bg-purple-500/10 border-purple-500/30' : 'text-muted-text hover:text-main-text'
            }`}
          >
            <Terminal className="w-4 h-4" />
          </button>
          <button 
            onClick={regenerateSession}
            title="Generate New Session ID"
            className="p-2 hover:bg-hover-bg rounded-lg border border-main-border hover:border-purple-500/50 transition-all text-muted-text hover:text-main-text"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button 
            onClick={handleClear}
            title="Clear Chat Logs"
            className="p-2 hover:bg-red-950/30 hover:border-red-500/30 border border-transparent rounded-lg text-red-400 transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Workspace split */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat Section */}
        <div className="flex-1 flex flex-col justify-between bg-chat-bg relative transition-colors duration-200">
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
                <div className="p-4 bg-purple-900/10 border border-purple-500/20 rounded-full text-purple-400">
                  <Bot className="w-12 h-12" />
                </div>
                <h3 className="text-lg font-semibold text-main-text">ResolveDesk AI Active</h3>
                <p className="text-sm text-muted-text">
                  Hello! I am your AI resolution copilot. Ask me about refund policies, subscription information, pricing plans, or client troubleshooting tickets.
                </p>
               
              </div>
            ) : (
              messages.map((msg, index) => (
                <div 
                  key={index}
                  className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-9 h-9 shrink-0 flex items-center justify-center rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
                      <Bot className="w-5 h-5" />
                    </div>
                  )}

                  <div className={`max-w-[75%] rounded-2xl p-4 shadow-md transition-all duration-200 ${
                    msg.role === 'user' 
                      ? 'bg-purple-600 text-white rounded-tr-none' 
                      : 'bg-card-bg border border-card-border text-main-text rounded-tl-none'
                  }`}>
                    <MarkdownRenderer content={msg.content} isUser={msg.role === 'user'} />
                    
                    {msg.role === 'assistant' && (
                      <div className="flex items-center justify-between mt-3 pt-2 border-t border-card-border text-[10px] text-muted-text transition-colors duration-200">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => handleFeedback(index, 'up')}
                            className={`p-1 hover:text-green-400 transition-all ${feedbackLog[index] === 'up' ? 'text-green-400' : ''}`}
                            title="Helpful Response"
                          >
                            <ThumbsUp className="w-3.5 h-3.5" />
                          </button>
                          <button 
                            onClick={() => handleFeedback(index, 'down')}
                            className={`p-1 hover:text-red-400 transition-all ${feedbackLog[index] === 'down' ? 'text-red-400' : ''}`}
                            title="Unhelpful/Incorrect"
                          >
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-9 h-9 shrink-0 flex items-center justify-center rounded-xl bg-hover-bg border border-main-border text-muted-text">
                      <User className="w-5 h-5" />
                    </div>
                  )}
                </div>
              ))
            )}

            {loading && (
              <div className="flex gap-4 justify-start">
                <div className="w-9 h-9 flex items-center justify-center rounded-xl bg-purple-900/30 border border-purple-500/30 text-purple-300">
                  <Bot className="w-5 h-5 animate-pulse" />
                </div>
                <div className="max-w-[70%] bg-card-bg border border-card-border rounded-2xl rounded-tl-none p-4 text-muted-text">
                  <div className="flex gap-1 items-center">
                    <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce"></span>
                    <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce delay-100"></span>
                    <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce delay-200"></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Form Input */}
          <form onSubmit={handleSend} className="px-6 py-4 bg-panel-bg/80 border-t border-main-border">
            <div className="relative flex items-center">
              <input 
                type="text" 
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about refunds, subscriptions, pricing..."
                disabled={loading}
                className="w-full bg-input-bg border border-main-border focus:border-purple-500/80 rounded-xl px-4 py-3.5 pr-12 outline-none text-sm transition-all placeholder-input-text text-main-text"
              />
              <button 
                type="submit"
                disabled={loading || !input.trim()}
                className="absolute right-3 p-2 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-950/50 disabled:text-purple-700 text-white rounded-lg transition-all cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Trace Console Panel (Right Sidebar) */}
        <aside className={`border-l border-main-border bg-panel-bg flex flex-col overflow-y-auto space-y-6 transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'w-80 md:w-96 p-6 opacity-100' : 'w-0 p-0 border-l-0 opacity-0 overflow-hidden'
        }`}>
          <div className="flex items-center gap-2 border-b border-main-border pb-3">
            <Terminal className="w-5 h-5 text-purple-400" />
            <h2 className="font-bold text-main-text text-sm uppercase tracking-wider">Agent Evaluation Trace</h2>
          </div>

          {/* Active Node */}
          <div className="space-y-2">
            <span className="text-[10px] text-muted-text uppercase tracking-wider font-semibold">Active Specialist Node</span>
            <div className="flex items-center gap-3 p-3 bg-input-bg border border-main-border rounded-xl">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></div>
              <span className="font-mono text-sm text-main-text font-semibold">{activeState.current_agent}</span>
            </div>
          </div>

          {/* Safety Check Badge */}
          <div className="space-y-2">
            <span className="text-[10px] text-muted-text uppercase tracking-wider font-semibold">Safety & Compliance</span>
            <div className={`flex items-start gap-3 p-3 border rounded-xl transition-all duration-200 ${
              activeState.safety_check.passed 
                ? 'bg-safety-pass-bg border-safety-pass-border text-safety-pass-text' 
                : 'bg-safety-fail-bg border-safety-fail-border text-safety-fail-text'
            }`}>
              {activeState.safety_check.passed ? (
                <ShieldCheck className="w-5 h-5 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
              )}
              <div className="text-xs">
                <p className="font-semibold">{activeState.safety_check.passed ? 'VERIFIED SAFE' : 'EXPLOIT FLAGGED'}</p>
                <p className="text-muted-text mt-0.5">{activeState.safety_check.details}</p>
              </div>
            </div>
          </div>

          {/* Planner steps */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-[10px] text-muted-text uppercase tracking-wider font-semibold">
              <ListChecks className="w-3.5 h-3.5 text-purple-400" />
              <span>Planner Tasks</span>
            </div>
            <div className="p-3.5 bg-input-bg border border-main-border rounded-xl space-y-2 text-xs">
              {activeState.plan_steps.length === 0 ? (
                <p className="text-input-text italic">No active task decomposition required.</p>
              ) : (
                activeState.plan_steps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2.5 text-main-text">
                    <CheckCircle2 className="w-4 h-4 text-purple-400 shrink-0" />
                    <span className="font-mono">{step}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Database Output */}
          <div className="space-y-2 flex-1 flex flex-col">
            <div className="flex items-center gap-1.5 text-[10px] text-muted-text uppercase tracking-wider font-semibold">
              <Database className="w-3.5 h-3.5 text-purple-400" />
              <span>Live Database Results</span>
            </div>
            <div className="flex-1 min-h-[150px] p-3.5 bg-input-bg border border-main-border rounded-xl font-mono text-xs text-main-text overflow-y-auto">
              {Object.keys(activeState.sql_results).length === 0 ? (
                <p className="text-input-text italic">No active database querying trace.</p>
              ) : (
                <pre className="whitespace-pre-wrap">{JSON.stringify(activeState.sql_results, null, 2)}</pre>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default App
