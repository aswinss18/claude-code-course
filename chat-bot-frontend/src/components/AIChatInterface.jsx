import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, RotateCcw, Copy, ThumbsUp, ThumbsDown, Sparkles } from 'lucide-react';

const AIChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your AI assistant. How can I help you today?",
      sender: 'ai',
      timestamp: new Date(Date.now() - 1000),
      isWelcome: true
    }
  ]);
  
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // API call to localhost:8000/chat
  const callAIAPI = async (userMessage) => {
    try {
      setError(null);

      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed with status: ${response.status}`);
      }

      const data = await response.json();
      return data.message;
    } catch (err) {
      console.error('API Error:', err);
      throw new Error('Failed to get AI response. Please check if the API server is running on localhost:8000.');
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: newMessage.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = newMessage.trim();
    setNewMessage('');
    setIsLoading(true);

    try {
      const aiResponse = await callAIAPI(currentMessage);
      
      const aiMessage = {
        id: Date.now() + 1,
        text: aiResponse,
        sender: 'ai',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      setError(err.message);
      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I'm having trouble responding right now. Please try again.",
        sender: 'ai',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopyMessage = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleRegenerateResponse = async (messageIndex) => {
    if (isLoading) return;
    
    const userMessage = messages[messageIndex - 1];
    if (!userMessage || userMessage.sender !== 'user') return;

    setIsLoading(true);
    try {
      const aiResponse = await callAIAPI(userMessage.text);
      
      setMessages(prev => prev.map((msg, idx) => 
        idx === messageIndex 
          ? { ...msg, text: aiResponse, timestamp: new Date() }
          : msg
      ));
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([{
      id: 1,
      text: "Hello! I'm your AI assistant. How can I help you today?",
      sender: 'ai',
      timestamp: new Date(),
      isWelcome: true
    }]);
    setError(null);
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.avatar}>
            <Bot size={24} color="white" />
          </div>
          <div>
            <h2 style={styles.title}>
              AI Assistant
              <Sparkles size={16} style={styles.sparkleIcon} />
            </h2>
            <p style={styles.status}>
              {isLoading ? 'Thinking...' : 'Ready to help'}
            </p>
          </div>
        </div>
        <button onClick={clearChat} style={styles.newChatButton}>
          <RotateCcw size={16} />
          New Chat
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={styles.errorBanner}>
          <p style={styles.errorText}>{error}</p>
        </div>
      )}

      {/* Messages */}
      <div style={styles.messagesContainer}>
        {messages.map((message, index) => (
          <div
            key={message.id}
            style={{
              ...styles.messageWrapper,
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div style={{
              ...styles.messageGroup,
              flexDirection: message.sender === 'user' ? 'row-reverse' : 'row'
            }}>
              {/* Avatar */}
              <div style={{
                ...styles.messageAvatar,
                background: message.sender === 'user' 
                  ? 'linear-gradient(135deg, #3b82f6, #2563eb)' 
                  : 'linear-gradient(135deg, #8b5cf6, #3b82f6)'
              }}>
                {message.sender === 'user' ? (
                  <User size={16} color="white" />
                ) : (
                  <Bot size={16} color="white" />
                )}
              </div>

              {/* Message Content */}
              <div style={styles.messageContent}>
                <div style={{
                  ...styles.messageBubble,
                  backgroundColor: message.sender === 'user' ? '#3b82f6' : '#ffffff',
                  color: message.sender === 'user' ? 'white' : '#1f2937',
                  borderBottomRightRadius: message.sender === 'user' ? '4px' : '16px',
                  borderBottomLeftRadius: message.sender === 'user' ? '16px' : '4px',
                  border: message.sender === 'ai' ? '1px solid #e5e7eb' : 'none',
                  ...(message.isError ? styles.errorMessage : {})
                }}>
                  <p style={styles.messageText}>
                    {message.text}
                  </p>
                </div>

                {/* Message Actions & Timestamp */}
                <div style={{
                  ...styles.messageFooter,
                  flexDirection: message.sender === 'user' ? 'row-reverse' : 'row'
                }}>
                  <div style={styles.timestamp}>
                    {formatTime(message.timestamp)}
                  </div>

                  {message.sender === 'ai' && !message.isWelcome && (
                    <div style={styles.messageActions}>
                      <button
                        onClick={() => handleCopyMessage(message.text)}
                        style={styles.actionButton}
                        title="Copy message"
                      >
                        <Copy size={12} />
                      </button>
                      <button
                        onClick={() => handleRegenerateResponse(index)}
                        disabled={isLoading}
                        style={{
                          ...styles.actionButton,
                          opacity: isLoading ? 0.5 : 1
                        }}
                        title="Regenerate response"
                      >
                        <RotateCcw size={12} />
                      </button>
                      <button style={styles.actionButton}>
                        <ThumbsUp size={12} />
                      </button>
                      <button style={styles.actionButton}>
                        <ThumbsDown size={12} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {/* Loading Indicator */}
        {isLoading && (
          <div style={styles.loadingWrapper}>
            <div style={styles.loadingGroup}>
              <div style={styles.loadingAvatar}>
                <Bot size={16} color="white" />
              </div>
              <div style={styles.loadingBubble}>
                <div style={styles.loadingDots}>
                  <div style={{...styles.dot, animationDelay: '0s'}}></div>
                  <div style={{...styles.dot, animationDelay: '0.1s'}}></div>
                  <div style={{...styles.dot, animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={styles.inputContainer}>
        <div style={styles.inputWrapper}>
          <div style={styles.textareaContainer}>
            <textarea
              ref={inputRef}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me anything..."
              disabled={isLoading}
              style={{
                ...styles.textarea,
                opacity: isLoading ? 0.5 : 1,
                cursor: isLoading ? 'not-allowed' : 'text'
              }}
              rows={1}
            />
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!newMessage.trim() || isLoading}
            style={{
              ...styles.sendButton,
              background: newMessage.trim() && !isLoading
                ? 'linear-gradient(135deg, #8b5cf6, #3b82f6)'
                : '#f3f4f6',
              color: newMessage.trim() && !isLoading ? 'white' : '#9ca3af',
              cursor: newMessage.trim() && !isLoading ? 'pointer' : 'not-allowed',
              transform: newMessage.trim() && !isLoading ? 'scale(1.05)' : 'scale(1)',
              boxShadow: newMessage.trim() && !isLoading ? '0 10px 15px -3px rgba(0, 0, 0, 0.1)' : 'none'
            }}
          >
            <Send size={20} />
          </button>
        </div>
        
        {/* Quick Actions */}
        <div style={styles.quickActions}>
          <span>Press Enter to send • Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    width: '100vw',
    background: 'linear-gradient(135deg, #f9fafb, #f3f4f6)',
    margin: 0,
    padding: 0,
    overflow: 'hidden',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  header: {
    backgroundColor: 'white',
    borderBottom: '1px solid #e5e7eb',
    padding: '12px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0,
    minHeight: '60px'
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  avatar: {
    width: '40px',
    height: '40px',
    background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  title: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1f2937',
    margin: 0,
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  sparkleIcon: {
    color: '#8b5cf6'
  },
  status: {
    fontSize: '14px',
    color: '#6b7280',
    margin: 0
  },
  newChatButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    fontSize: '14px',
    color: '#6b7280',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  errorBanner: {
    backgroundColor: '#fef2f2',
    borderLeft: '4px solid #f87171',
    padding: '12px 20px',
    margin: '0 20px 16px',
    borderRadius: '8px',
    flexShrink: 0
  },
  errorText: {
    color: '#b91c1c',
    fontSize: '14px',
    margin: 0
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    minHeight: 0
  },
  messageWrapper: {
    display: 'flex'
  },
  messageGroup: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    maxWidth: '70%',
    width: 'fit-content'
  },
  messageAvatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  messageContent: {
    flex: 1
  },
  messageBubble: {
    padding: '12px 16px',
    borderRadius: '16px',
    wordWrap: 'break-word',
    overflowWrap: 'break-word'
  },
  messageText: {
    fontSize: '14px',
    lineHeight: '1.5',
    margin: 0,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  },
  errorMessage: {
    borderColor: '#fca5a5',
    backgroundColor: '#fef2f2'
  },
  messageFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: '8px'
  },
  timestamp: {
    fontSize: '12px',
    color: '#6b7280'
  },
  messageActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  actionButton: {
    padding: '4px',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    color: '#9ca3af',
    transition: 'all 0.2s',
    ':hover': {
      backgroundColor: '#f3f4f6'
    }
  },
  loadingWrapper: {
    display: 'flex',
    justifyContent: 'flex-start'
  },
  loadingGroup: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px'
  },
  loadingAvatar: {
    width: '32px',
    height: '32px',
    background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  loadingBubble: {
    backgroundColor: 'white',
    border: '1px solid #e5e7eb',
    borderRadius: '16px',
    borderBottomLeftRadius: '4px',
    padding: '12px 16px'
  },
  loadingDots: {
    display: 'flex',
    gap: '4px'
  },
  dot: {
    width: '8px',
    height: '8px',
    backgroundColor: '#9ca3af',
    borderRadius: '50%',
    animation: 'bounce 1.4s ease-in-out infinite both'
  },
  inputContainer: {
    backgroundColor: 'white',
    borderTop: '1px solid #e5e7eb',
    padding: '16px 20px',
    flexShrink: 0
  },
  inputWrapper: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '12px'
  },
  textareaContainer: {
    flex: 1,
    position: 'relative'
  },
  textarea: {
    width: '100%',
    padding: '12px 16px',
    border: '1px solid #d1d5db',
    borderRadius: '16px',
    outline: 'none',
    resize: 'none',
    maxHeight: '120px',
    minHeight: '44px',
    fontSize: '14px',
    fontFamily: 'inherit',
    transition: 'all 0.2s',
    lineHeight: '1.4',
    boxSizing: 'border-box'
  },
  sendButton: {
    padding: '12px',
    borderRadius: '50%',
    border: 'none',
    transition: 'all 0.2s',
    flexShrink: 0
  },
  quickActions: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: '8px',
    fontSize: '12px',
    color: '#6b7280',
    userSelect: 'none'
  }
};

// Add CSS for full screen and animations
const styleSheet = document.styleSheets[0];
if (styleSheet) {
  try {
    // Global styles for full screen
    styleSheet.insertRule(`
      * {
        box-sizing: border-box;
      }
    `, styleSheet.cssRules.length);

    styleSheet.insertRule(`
      html, body {
        margin: 0;
        padding: 0;
        height: 100%;
        overflow: hidden;
      }
    `, styleSheet.cssRules.length);

    styleSheet.insertRule(`
      #root {
        height: 100vh;
        width: 100vw;
      }
    `, styleSheet.cssRules.length);

    // Loading animation
    styleSheet.insertRule(`
      @keyframes bounce {
        0%, 80%, 100% {
          transform: scale(0);
        }
        40% {
          transform: scale(1);
        }
      }
    `, styleSheet.cssRules.length);

    // Focus styles for textarea
    styleSheet.insertRule(`
      textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
      }
    `, styleSheet.cssRules.length);

    // Hover styles for action buttons
    styleSheet.insertRule(`
      button:hover {
        background-color: #f3f4f6;
      }
    `, styleSheet.cssRules.length);

  } catch (e) {
    // Ignore if rules already exist
  }
}

export default AIChatInterface;