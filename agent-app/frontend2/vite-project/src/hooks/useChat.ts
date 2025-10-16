import { useState, useCallback, useRef } from "react";

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

const createLocalPreview = (file: File) =>
  new Promise<DisplayFile>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve({
        name: file.name,
        type: file.type,
        url: reader.result as string,
      });
    };
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });

const base64ToBlobUrl = (base64Data: string, mimeType: string) => {
  const base64Content = base64Data.split(",")[1] || base64Data;
  const byteCharacters = atob(base64Content);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  const blob = new Blob([byteArray], { type: mimeType });
  return URL.createObjectURL(blob);
};

const readFileAsBase64OrText = (file: File) =>
  new Promise<{ name: string; type: string; data: string }>(
    (resolve, reject) => {
      const reader = new FileReader();

      if (file.type === "text/csv" || file.type === "text/plain") {
        reader.readAsText(file);
      } else {
        reader.readAsDataURL(file);
      }

      reader.onload = () => {
        let result = reader.result as string;

        if (!file.type.startsWith("text/") && result.includes(",")) {
          const [, base64] = result.split(",");
          result = base64;
        }

        resolve({
          name: file.name,
          type: file.type,
          data: result,
        });
      };

      reader.onerror = (err) => reject(err);
    }
  );

export function useChat(apiBaseUrl: string) {
  const [userId, setUserId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [appName, setAppName] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageWithAgent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [displayData, setDisplayData] = useState<string | null>(null);
  const [messageEvents, setMessageEvents] = useState<
    Map<string, ProcessedEvent[]>
  >(new Map());
  const [websiteCount, setWebsiteCount] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const createSession = async () => {
    const response = await fetch(
      apiBaseUrl + `/apps/app/users/u_999/sessions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );
    if (!response.ok)
      throw new Error(`Failed to create session. Status: ${response.status}`);
    return response.json();
  };

  const handleSubmit = async (query: string, files: File[]) => {
    if ((!query.trim() && files.length === 0) || isLoading) return;
    setIsLoading(true);

    const aiMessageId = Date.now().toString() + "_ai";
    const userMessageId = Date.now().toString();

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

      const displayFiles = await Promise.all(files.map(createLocalPreview));

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

      const fileParts = await Promise.all(
        files.map(async (file) => {
          try {
            const fileData = await readFileAsBase64OrText(file);
            return {
              inlineData: {
                displayName: fileData.name,
                data: fileData.data,
                mimeType:
                  fileData.type === "text/csv" ? "text/csv" : fileData.type,
              },
            };
          } catch (err) {
            console.error(`Failed to read file ${file.name}:`, err);
            return null;
          }
        })
      );
      const validFileParts = fileParts.filter(Boolean);

      const messageParts = [];
      if (query.trim()) messageParts.push({ text: query });
      messageParts.push(...validFileParts);

      const payload = {
        appName: currentAppName,
        userId: currentUserId,
        sessionId: currentSessionId,
        newMessage: { parts: messageParts, role: "user" },
        streaming: true,
      };

      console.log("--- Sending RUN_SSE Payload ---", payload);

      abortControllerRef.current = new AbortController();
      const response = await fetch(apiBaseUrl + `/run_sse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok || !response.body)
        throw new Error(`API call failed with status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let combinedContent = "";
      let finalAuthor = "unknown";
      let aiFiles: DisplayFile[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk
          .split("\n")
          .filter((line) => line.startsWith("data: "));

        for (const line of lines) {
          const jsonText = line.substring(5).trim();
          if (!jsonText) continue;

          try {
            const json = JSON.parse(jsonText);

            if (json.error) throw new Error(json.error.message || json.error);

            const textParts = json?.content?.parts
              ?.map((p: any) => p.text)
              .filter(Boolean)
              .join(" ");
            if (textParts) combinedContent += textParts;

            finalAuthor = json.author || finalAuthor;

            // Handle files
            if (json?.content?.parts) {
              json.content.parts.forEach((p: any) => {
                if (p.fileData) {
                  let fileUrl = p.fileData.fileUri;
                  if (fileUrl.startsWith("data:")) {
                    fileUrl = base64ToBlobUrl(fileUrl, p.fileData.mimeType);
                  }
                  aiFiles.push({
                    name: p.fileData.displayName,
                    type: p.fileData.mimeType,
                    url: fileUrl,
                  });
                }
              });
            }
          } catch (e) {
            console.error("Could not parse chunk:", jsonText);
          }
        }

        // ------------------ Update AI message live ------------------
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId
              ? {
                  ...m,
                  content: combinedContent,
                  agent: finalAuthor,
                  files: aiFiles,
                }
              : m
          )
        );
      }

      if (!combinedContent && aiFiles.length === 0) {
        throw new Error("No valid content received from server.");
      }
    } catch (err: any) {
      console.error("Error during handleSubmit:", err);
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

  // ------------------ Cancel / clear ------------------
  const handleCancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
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
