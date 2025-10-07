import { useState, useRef, useCallback } from "react";

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
  new Promise<{ dataUrl: string; base64Data: string; mimeType: string; name: string }>((resolve, reject) => {
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
  const [displayData, setDisplayData] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [messageEvents, setMessageEvents] = useState<Map<string, ProcessedEvent[]>>(new Map());
  const [websiteCount, setWebsiteCount] = useState(0);

  const currentAgentRef = useRef("");
  const accumulatedTextRef = useRef("");

  const retryWithBackoff = async (fn: () => Promise<any>, maxRetries = 10, maxDuration = 120000) => {
    const start = Date.now();
    let lastError: any;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      if (Date.now() - start > maxDuration) throw new Error("Retry timeout");
      try {
        return await fn();
      } catch (err) {
        lastError = err;
        await new Promise((r) => setTimeout(r, Math.min(1000 * 2 ** attempt, 5000)));
      }
    }
    throw lastError;
  };

  const createSession = async () => {
    const response = await fetch(apiBaseUrl + `/apps/app/users/u_999/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new Error("Failed to create session");
    return response.json();
  };

  const processSseEventData = (jsonData: string, aiMessageId: string) => {
    try {
      const parsed = JSON.parse(jsonData);
      const textParts = parsed.content?.parts?.filter((p: any) => p.text).map((p: any) => p.text) || [];

      if (textParts.length && parsed.author === "interactive_planner_agent") {
        for (const t of textParts) {
          accumulatedTextRef.current += t + " ";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMessageId ? { ...m, content: accumulatedTextRef.current.trim(), agent: parsed.author } : m
            )
          );
          setDisplayData(accumulatedTextRef.current.trim());
        }
      }
    } catch (e) {
      console.error("Failed SSE parse:", e, jsonData.slice(0, 200));
    }
  };

  const handleSubmit = useCallback(
    async (query: string, files: File[]) => {
      if (!query.trim() && files.length === 0) return;
      setIsLoading(true);

      try {
        let currentUserId = userId,
          currentSessionId = sessionId,
          currentAppName = appName;

        if (!currentSessionId || !currentUserId || !currentAppName) {
          const sessionData = await retryWithBackoff(createSession);
          setUserId(sessionData.userId);
          setSessionId(sessionData.id);
          setAppName(sessionData.appName);
          currentUserId = sessionData.userId;
          currentSessionId = sessionData.id;
          currentAppName = sessionData.appName;
        }

        const processedFiles = await Promise.all(files.map(readFileAsBase64));
        const displayFiles: DisplayFile[] = processedFiles.map((pf) => ({
          name: pf.name,
          type: pf.mimeType,
          url: pf.dataUrl,
        }));

        const userMessageId = Date.now().toString();
        setMessages((prev) => [...prev, { type: "human", content: query, id: userMessageId, files: displayFiles }]);

        const aiMessageId = Date.now().toString() + "_ai";
        accumulatedTextRef.current = "";
        setMessages((prev) => [...prev, { type: "ai", content: "", id: aiMessageId }]);

        const response = await fetch(apiBaseUrl + `/run_sse`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            appName: currentAppName,
            userId: currentUserId,
            sessionId: currentSessionId,
            newMessage: { parts: [{ text: query }], role: "user" },
            streaming: false,
          }),
        });
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let buf = "",
          eventBuf = "";

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (value) buf += decoder.decode(value, { stream: true });
            let idx;
            while ((idx = buf.indexOf("\n")) >= 0 || (done && buf.length > 0)) {
              let line: string;
              if (idx >= 0) {
                line = buf.slice(0, idx);
                buf = buf.slice(idx + 1);
              } else {
                line = buf;
                buf = "";
              }
              if (line.trim() === "") {
                if (eventBuf.length) {
                  processSseEventData(eventBuf, aiMessageId);
                  eventBuf = "";
                }
              } else if (line.startsWith("data:")) {
                eventBuf += line.slice(5).trimStart() + "\n";
              }
            }
            if (done) break;
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    },
    [userId, sessionId, appName]
  );

  const handleCancel = useCallback(() => {
    setMessages([]);
    setDisplayData(null);
    setMessageEvents(new Map());
    setWebsiteCount(0);
    window.location.reload();
  }, []);

  return { messages, isLoading, displayData, messageEvents, websiteCount, handleSubmit, handleCancel };
}
