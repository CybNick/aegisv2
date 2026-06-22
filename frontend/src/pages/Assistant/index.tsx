import { useState } from 'react';
import { Send, Sparkles, AlertCircle, ShieldCheck } from 'lucide-react';

export default function Assistant() {
  const [prompt, setPrompt] = useState("");
  const [conversation, setConversation] = useState<any[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  
  const handleAsk = async (text: string) => {
    if (!text.trim()) return;
    
    // Add user message
    setConversation(prev => [...prev, { role: 'user', text }]);
    setPrompt("");
    setIsTyping(true);
    
    try {
      const response = await fetch('/api/v1/assistant/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: text })
      });
      const data = await response.json();
      
      setConversation(prev => [...prev, { role: 'assistant', data: data.data.response }]);
    } catch (error) {
      setConversation(prev => [...prev, { role: 'assistant', error: 'Failed to communicate with intelligence engine.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const suggestions = [
    "What changed today?",
    "Show exposed assets",
    "What is my highest risk?",
    "Who owns the payment platform?",
    "Are we compliant?",
    "Generate executive summary"
  ];

  return (
    <div className="flex flex-col h-full bg-background relative overflow-hidden">
      <div className="flex-1 overflow-y-auto p-8 pb-32">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center mb-12">
            <Sparkles className="mx-auto text-primary mb-4" size={48} />
            <h1 className="text-4xl font-bold mb-2">Aegis Intelligence</h1>
            <p className="text-secondary text-lg">Ask any question. Get deterministic, evidence-backed answers.</p>
          </div>

          {conversation.length === 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {suggestions.map((s, i) => (
                <button 
                  key={i} 
                  className="card p-4 text-left hover:border-primary transition-colors bg-tertiary/50"
                  onClick={() => handleAsk(s)}
                >
                  <span className="font-medium text-secondary">{s}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              {conversation.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'user' ? (
                    <div className="bg-primary/10 text-foreground px-6 py-3 rounded-2xl rounded-tr-none border border-primary/20 max-w-2xl">
                      {msg.text}
                    </div>
                  ) : msg.error ? (
                    <div className="bg-danger/10 text-danger px-6 py-3 rounded-2xl rounded-tl-none border border-danger/20 max-w-2xl flex items-center gap-2">
                      <AlertCircle size={18} /> {msg.error}
                    </div>
                  ) : (
                    <div className="bg-tertiary text-foreground p-6 rounded-2xl rounded-tl-none border border-border max-w-3xl w-full shadow-lg">
                      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <ShieldCheck className="text-success" /> {msg.data.title}
                      </h3>
                      
                      <div className="space-y-4">
                        {msg.data.findings.map((f: any, idx: number) => (
                          <div key={idx} className="bg-background border border-border rounded p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <span className={`badge ${f.severity === 'CRITICAL' ? 'badge-primary' : 'badge-outline'}`}>{f.severity}</span>
                              <h4 className="font-bold text-lg">{f.title}</h4>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                              <div>
                                <div className="text-xs font-bold text-secondary uppercase mb-1">Evidence</div>
                                <div className="text-sm font-mono bg-tertiary p-2 rounded">{f.evidence}</div>
                              </div>
                              <div>
                                <div className="text-xs font-bold text-secondary uppercase mb-1">Action</div>
                                <div className="text-sm bg-primary/5 text-primary p-2 rounded border border-primary/20 font-medium">{f.action}</div>
                              </div>
                            </div>
                            {f.affected_assets && f.affected_assets.length > 0 && (
                              <div className="mt-3 text-xs text-secondary">
                                <strong>Affected:</strong> {f.affected_assets.join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 pt-4 border-t border-border flex justify-between items-center text-xs text-secondary">
                        <span>Confidence: {(msg.data.confidence * 100).toFixed(0)}% (Deterministic)</span>
                        <span>Derived strictly from current GraphView.</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-tertiary text-secondary px-6 py-3 rounded-2xl rounded-tl-none border border-border animate-pulse">
                    Analyzing graph data...
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background to-transparent">
        <div className="max-w-4xl mx-auto flex items-center gap-4 bg-tertiary border border-primary/30 p-2 rounded-full shadow-2xl focus-within:border-primary transition-colors">
          <input 
            type="text" 
            placeholder="Ask Aegis..." 
            className="flex-1 bg-transparent border-none outline-none px-6 py-3 text-lg"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAsk(prompt)}
          />
          <button 
            className="bg-primary text-primary-foreground p-3 rounded-full hover:brightness-110 transition-all disabled:opacity-50"
            onClick={() => handleAsk(prompt)}
            disabled={!prompt.trim() || isTyping}
          >
            <Send size={24} />
          </button>
        </div>
      </div>
    </div>
  );
}
