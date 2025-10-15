import { useState, useCallback } from "react";

export interface DisplayFile {
  name: string;
  type: string;
  url: string;
}
export interface MessageWithAgent {
  type: "human" | "ai";
  content: string;
  id: string;
  agent?: string;
  finalReportWithCitations?: boolean;
  files?: DisplayFile[];
}
export interface ProcessedEvent {
  title: string;
  data: any;
}

const readFileAsBase64 = (file: File) =>
  new Promise<{
    dataUrl: string;
    base64Data: string;
    mimeType: string;
    name: string;
  }>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      resolve({
        dataUrl,
        base64Data: dataUrl.split(",")[1],
        mimeType: file.type,
        name: file.name,
      });
    };
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });

export function useChat(apiBaseUrl: string) {
  const [userId, setUserId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [appName, setAppName] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageWithAgent[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [displayData] = useState<string | null>(null);
  const [messageEvents] = useState<Map<string, ProcessedEvent[]>>(new Map());
  const [websiteCount] = useState(0);

  const createSession = async () => {
    const response = await fetch(
      apiBaseUrl + `/apps/app/users/u_999/sessions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to create session. Status: ${response.status}`);
    }
    return response.json();
  };

  const handleSubmit = async (query: string, files: File[]) => {
    if ((!query.trim() && files.length === 0) || isLoading) return;
    setIsLoading(true);

    const aiMessageId = Date.now().toString() + "_ai";

    try {
      let currentSessionId = sessionId;
      let currentUserId = userId;
      let currentAppName = appName;

      if (!currentSessionId || !currentUserId || !currentAppName) {
        const sessionData = await createSession();
        setUserId(sessionData.userId);
        setSessionId(sessionData.id);
        setAppName(sessionData.appName);
        currentSessionId = sessionData.id;
        currentUserId = sessionData.userId;
        currentAppName = sessionData.appName;
      }

      const processedFiles = await Promise.all(files.map(readFileAsBase64));
      const displayFiles: DisplayFile[] = processedFiles.map((pf) => ({
        name: pf.name,
        type: pf.mimeType,
        url: pf.dataUrl,
      }));

      const userMessageId = Date.now().toString();
      setMessages((prev) => [
        ...prev,
        {
          type: "human",
          content: query,
          id: userMessageId,
          files: displayFiles,
        },
        { type: "ai", content: "", id: aiMessageId },
      ]);
      const messageParts = [{ text: query }];

      for (const file of processedFiles) {
        messageParts.push({ text: file.dataUrl });
      }

      const response = await fetch(apiBaseUrl + `/run_sse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          appName: currentAppName,
          userId: currentUserId,
          sessionId: currentSessionId,
          newMessage: { parts: messageParts, role: "user" },
          streaming: false,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponseText = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        fullResponseText += decoder.decode(value, { stream: true });
      }
      const lines = fullResponseText
        .split("\n")
        .filter((line) => line.startsWith("data: "));
      let combinedContent = "";
      let finalAuthor = "unknown";
      for (const line of lines) {
        const jsonText = line.substring(5).trim();
        if (jsonText) {
          try {
            const jsonResponse = JSON.parse(jsonText);
            const textPart = jsonResponse?.content?.parts?.[0]?.text;
            if (typeof textPart === "string") {
              combinedContent += textPart;
              finalAuthor = jsonResponse.author || finalAuthor;
            }
          } catch (e) {
            console.error("Could not parse a JSON chunk:", jsonText);
          }
        }
      }
      if (combinedContent) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId
              ? { ...m, content: combinedContent, agent: finalAuthor }
              : m
          )
        );
      } else {
        throw new Error(
          "Could not extract any valid content from the server response."
        );
      }
    } catch (err: any) {
      console.error("An error occurred during handleSubmit:", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId
            ? { ...m, content: `An error occurred: ${err.message}` }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = useCallback(() => {
    window.location.reload();
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    displayData,
    messageEvents,
    websiteCount,
    handleSubmit,
    handleCancel,
    clearChat,
  };
}
