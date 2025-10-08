import React from "react";
import { ChatMessagesView } from "../components/ChatMessagesView";
import { useChatContext } from "../contexts/ChatContext";

const Chat: React.FC = () => {
  const { messages, isLoading, handleSubmit } = useChatContext();

  return (
    <ChatMessagesView
      messages={messages}
      isLoading={isLoading}
      onSubmit={handleSubmit}
    />
  );
};

export default Chat;
