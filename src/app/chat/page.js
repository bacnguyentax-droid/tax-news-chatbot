'use client';

import { useState, useEffect, useRef } from 'react';

// Format chatbot output to clean styled HTML
function formatBotResponse(text) {
  if (!text) return '';
  const lines = text.split('\n');
  let html = [];
  let inList = false;

  for (let line of lines) {
    let trimmed = line.trim();
    
    // List item (starts with * or -)
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!inList) {
        html.push('<ul style="padding-left: 20px; margin-bottom: 12px; list-style-type: disc;">');
        inList = true;
      }
      const itemText = trimmed.substring(2)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
      html.push(`<li style="margin-bottom: 6px;">${itemText}</li>`);
      continue;
    } else if (inList && !trimmed.startsWith('* ') && !trimmed.startsWith('- ') && trimmed !== '') {
      html.push('</ul>');
      inList = false;
    }

    // Headers
    if (trimmed.startsWith('### ')) {
      html.push(`<h4 style="margin: 18px 0 8px 0; font-weight: 700; font-size: 1.05rem;">${trimmed.substring(4).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</h4>`);
    } else if (trimmed.startsWith('## ')) {
      html.push(`<h3 style="margin: 24px 0 10px 0; font-weight: 700; font-size: 1.2rem; border-bottom: 1px solid var(--border); padding-bottom: 6px;">${trimmed.substring(3).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</h3>`);
    } else if (trimmed.startsWith('# ')) {
      html.push(`<h2 style="margin: 28px 0 12px 0; font-weight: 700; font-size: 1.35rem;">${trimmed.substring(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</h2>`);
    } else if (trimmed === '') {
      continue;
    } else {
      // Normal paragraph
      const formatted = trimmed
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
      html.push(`<p style="margin-bottom: 12px; line-height: 1.6;">${formatted}</p>`);
    }
  }

  if (inList) {
    html.push('</ul>');
  }

  return html.join('\n');
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [qasCount, setQasCount] = useState(0);
  
  const chatWindowRef = useRef(null);

  // Quick prompt templates
  const quickPrompts = [
    'Hộ kinh doanh mới thành lập nộp thuế gì?',
    'Doanh thu dưới 100 triệu nộp bao nhiêu thuế?',
    'Thời hạn nộp tờ khai thuế khoán năm là khi nào?',
    'Tỷ lệ tính thuế khoán phân phối hàng hóa?'
  ];

  // Fetch loaded documents for sidebar on mount
  useEffect(() => {
    async function fetchSidebarData() {
      try {
        const [pdfRes, qaRes] = await Promise.all([
          fetch('/api/admin/pdf'),
          fetch('/api/admin/qa')
        ]);
        if (pdfRes.ok) {
          const pdfData = await pdfRes.json();
          setDocuments(pdfData);
        }
        if (qaRes.ok) {
          const qaData = await qaRes.json();
          setQasCount(qaData.length);
        }
      } catch (err) {
        console.error('Lỗi khi tải thông tin tài liệu:', err);
      }
    }
    fetchSidebarData();

    // Load conversation history from sessionStorage if available
    const storedHistory = sessionStorage.getItem('tax_chat_history');
    if (storedHistory) {
      setMessages(JSON.parse(storedHistory));
    }
  }, []);

  // Auto scroll chat to bottom when messages update
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const saveHistory = (updatedMessages) => {
    setMessages(updatedMessages);
    sessionStorage.setItem('tax_chat_history', JSON.stringify(updatedMessages));
  };

  const handleSend = async (textToSend) => {
    const queryText = textToSend || input;
    if (!queryText.trim() || isLoading) return;

    // Clear input
    if (!textToSend) setInput('');

    // Append user message
    const userMessage = { role: 'user', content: queryText };
    const updatedMessages = [...messages, userMessage];
    saveHistory(updatedMessages);
    setIsLoading(true);

    try {
      // Call chat API
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: queryText,
          history: updatedMessages.slice(0, -1) // Send history excluding the latest user message
        })
      });

      const data = await res.json();

      if (res.ok) {
        // Append bot message with sources
        const botMessage = {
          role: 'model',
          content: data.text,
          sources: data.sources || []
        };
        saveHistory([...updatedMessages, botMessage]);
      } else {
        const botMessage = {
          role: 'model',
          content: `❌ Lỗi: ${data.error || 'Không thể lấy câu trả lời.'}`
        };
        saveHistory([...updatedMessages, botMessage]);
      }
    } catch (err) {
      console.error(err);
      const botMessage = {
        role: 'model',
        content: `❌ Đã xảy ra lỗi kết nối: ${err.message}`
      };
      saveHistory([...updatedMessages, botMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = () => {
    if (window.confirm('Bạn có muốn xóa toàn bộ lịch sử cuộc trò chuyện này không?')) {
      setMessages([]);
      sessionStorage.removeItem('tax_chat_history');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-page">
      {/* Sidebar - Shows context files chatbot is trained on */}
      <aside className="chat-sidebar animate-fade">
        <div>
          <h3 className="sidebar-title" style={{ marginBottom: '16px' }}>Cơ sở tri thức</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--muted)', lineHeight: 1.4, marginBottom: '20px' }}>
            Chatbot trả lời <strong>duy nhất</strong> dựa trên các tài liệu thuế và câu hỏi Q&A do Admin tải lên dưới đây:
          </p>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', color: 'var(--foreground)', display: 'flex', justifyContent: 'space-between' }}>
              <span>VĂN BẢN PHÁP LUẬT (PDF)</span>
              <span className="badge badge-primary" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>{documents.length}</span>
            </h4>
            <div className="doc-list">
              {documents.length === 0 ? (
                <div style={{ padding: '12px', border: '1px dashed var(--border)', borderRadius: 'var(--radius-sm)', textAlign: 'center', color: 'var(--muted)', fontSize: '0.8rem' }}>
                  Chưa có tài liệu PDF nào
                </div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} className="doc-item" title={doc.name}>
                    📄 {doc.name}
                  </div>
                ))
              )}
            </div>
          </div>

          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', color: 'var(--foreground)', display: 'flex', justifyContent: 'space-between' }}>
              <span>BỘ CÂU HỎI Q&A</span>
              <span className="badge badge-primary" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>{qasCount}</span>
            </h4>
            <div className="doc-item">
              ❓ {qasCount} câu hỏi/đáp đã nạp
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', fontSize: '0.75rem', color: 'var(--muted)', textAlign: 'center' }}>
          Mô hình: <strong>Gemini 2.5 Flash</strong>
        </div>
      </aside>

      {/* Main Chat Interface */}
      <div className="chat-main">
        {/* Chat header */}
        <div className="chat-header-info">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: 'var(--success)', borderRadius: '50%', display: 'inline-block' }}></span>
            <h2 style={{ fontSize: '1.05rem', margin: 0, fontWeight: 700 }}>Trợ lý ảo Tư vấn Thuế Hộ kinh doanh</h2>
          </div>
          
          {messages.length > 0 && (
            <button onClick={clearHistory} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
              🗑️ Xóa lịch sử
            </button>
          )}
        </div>

        {/* Messages List */}
        <div className="chat-window" ref={chatWindowRef}>
          {messages.length === 0 ? (
            <div className="chat-empty-state animate-slide-up">
              <div className="logo-icon" style={{ width: '56px', height: '56px', fontSize: '1.5rem', borderRadius: 'var(--radius)', marginBottom: '10px' }}>💬</div>
              <h1 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Tôi có thể giúp gì cho hộ kinh doanh của bạn?</h1>
              <p style={{ color: 'var(--muted)', lineHeight: 1.6, fontSize: '0.975rem', marginBottom: '10px' }}>
                Hệ thống chatbot trả lời tự động dựa trên tài liệu văn bản pháp quy được nạp chính thức. Vui lòng chọn một câu hỏi gợi ý bên dưới hoặc tự nhập câu hỏi của bạn.
              </p>

              <div className="quick-prompts-grid">
                {quickPrompts.map((prompt, idx) => (
                  <button 
                    key={idx} 
                    className="quick-prompt-btn"
                    onClick={() => handleSend(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message-bubble-wrapper ${msg.role === 'user' ? 'user' : 'bot'} animate-fade`}>
                <div className="message-bubble">
                  {msg.role === 'user' ? (
                    <p style={{ margin: 0 }}>{msg.content}</p>
                  ) : (
                    <>
                      <div dangerouslySetInnerHTML={{ __html: formatBotResponse(msg.content) }} />
                      
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
                            <path d="M12 16v-4"></path>
                            <path d="M12 8h.01"></path>
                          </svg>
                          <span>Nguồn trích dẫn: <strong>{msg.sources.map(s => s.name).join(', ')}</strong></span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="message-bubble-wrapper bot animate-fade">
              <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Đang tìm câu trả lời</span>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            <textarea
              className="chat-textarea"
              placeholder="Nhập câu hỏi về thuế của bạn tại đây (Nhấn Enter để gửi)..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              className="chat-send-btn"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              title="Gửi câu hỏi"
              aria-label="Send message"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
          <div style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--muted)', marginTop: '8px' }}>
            Lưu ý: Chatbot chỉ trả lời dựa trên tài liệu pháp quy được huấn luyện. Trường hợp không có dữ liệu, bot sẽ từ chối trả lời.
          </div>
        </div>
      </div>
    </div>
  );
}
