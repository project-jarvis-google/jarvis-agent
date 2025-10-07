import { useRef, useEffect } from "react";
import { useBackendHealth } from "@/hooks/useBackendHealth";
import { useChat } from "@/hooks/useChat";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { BackendLoadingScreen } from "@/components/BackendLoadingScreen";
import { BackendUnavailable } from "@/components/BackendUnavailable";

const API_BASE_URL = "http://localhost:8000";

export default function App() {
  const { isBackendReady, isCheckingBackend } = useBackendHealth(API_BASE_URL);
  const { messages, isLoading, displayData, messageEvents, websiteCount, handleSubmit, handleCancel } =
    useChat(API_BASE_URL);

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (viewport) viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className={`flex-1 overflow-y-auto ${messages.length === 0 || isCheckingBackend ? "flex" : ""}`}>
          {isCheckingBackend ? (
            <BackendLoadingScreen />
          ) : !isBackendReady ? (
            <BackendUnavailable />
          ) : messages.length === 0 ? (
            <WelcomeScreen handleSubmit={handleSubmit} isLoading={isLoading} onCancel={handleCancel} />
          ) : (
            <ChatMessagesView
              messages={messages}
              isLoading={isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              displayData={displayData}
              messageEvents={messageEvents}
              websiteCount={websiteCount}
            />
          )}
        </div>
      </main>
    </div>
  );
}
