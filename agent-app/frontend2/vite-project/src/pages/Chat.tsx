import React from 'react';
import { ChatMessagesView } from '../components/ChatMessagesView';
import { useChatContext } from '../contexts/ChatContext';

const Chat: React.FC = () => {
  const { 
    messages, 
    isLoading, 
    handleSubmit, 
    onCancel 
  } = useChatContext();

  return (
    <ChatMessagesView
      messages={messages}
      isLoading={isLoading}
      onCancel={onCancel}
      onSubmit={handleSubmit}
    />
  );
};

export default Chat;