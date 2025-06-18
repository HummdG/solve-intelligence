// ===== TASK 2: REAL-TIME AI SUGGESTIONS - Enhanced Document Component =====
// File: client/src/Document.tsx
import Editor from "./internal/Editor";
import SuggestionsSidebar, {
  AISuggestion,
  SuggestionsData,
  WebSocketMessage,
} from "./SuggestionsSidebar";
import useWebSocket from "react-use-websocket";
import { debounce } from "lodash";
import { useCallback, useEffect, useState } from "react";

export interface DocumentProps {
  onContentChange: (content: string) => void;
  content: string;
}

const SOCKET_URL = "ws://localhost:8000/ws";

export default function Document({ onContentChange, content }: DocumentProps) {
  const [messageHistory, setMessageHistory] = useState<MessageEvent[]>([]);

  // ===== TASK 2: REAL-TIME AI SUGGESTIONS - New State for AI Suggestions =====
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([]);
  const [isProcessingAI, setIsProcessingAI] = useState<boolean>(false);
  const [aiError, setAiError] = useState<string | null>(null);
  // ===== END TASK 2 =====

  const { sendMessage, lastMessage } = useWebSocket(SOCKET_URL, {
    onOpen: () => {
      console.log("WebSocket Connected");
      setAiError(null);
    },
    onClose: () => {
      console.log("WebSocket Disconnected");
      setIsProcessingAI(false);
    },
    onError: (event) => {
      console.error("WebSocket Error:", event);
      setAiError("Connection error occurred");
      setIsProcessingAI(false);
    },
    shouldReconnect: (_closeEvent) => true,
    reconnectAttempts: 3,
    reconnectInterval: 3000,
  });

  // ===== TASK 2: REAL-TIME AI SUGGESTIONS - Enhanced WebSocket Message Handling =====
  useEffect(() => {
    if (lastMessage !== null) {
      setMessageHistory((prev) => prev.concat(lastMessage));

      try {
        // Parse the incoming WebSocket message
        const message: WebSocketMessage = JSON.parse(lastMessage.data);
        console.log("Received WebSocket message:", message);

        // Handle different message types
        switch (message.type) {
          case "status":
            if (message.status === "processing") {
              setIsProcessingAI(true);
              setAiError(null);
            }
            break;

          case "suggestions":
            if (message.status === "success" && message.data) {
              const suggestionsData = message.data as SuggestionsData;
              setAiSuggestions(suggestionsData.issues || []);
              setIsProcessingAI(false);
              setAiError(null);
              console.log("Updated AI suggestions:", suggestionsData.issues);
            }
            break;

          case "error":
            const errorData = message.data as { message: string };
            setAiError(errorData.message || "An error occurred");
            setIsProcessingAI(false);
            setAiSuggestions([]);
            console.error("AI processing error:", errorData.message);
            break;

          default:
            console.warn("Unknown message type:", message.type);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
        setAiError("Failed to parse server response");
        setIsProcessingAI(false);
      }
    }
  }, [lastMessage, setMessageHistory]);
  // ===== END TASK 2 =====

  // ===== TASK 2: REAL-TIME AI SUGGESTIONS - Enhanced Content Change Handler =====
  // Debounce editor content changes for AI analysis
  const sendEditorContent = useCallback(
    debounce((content: string) => {
      if (content.trim()) {
        console.log("Sending content to AI for analysis");
        setIsProcessingAI(true);
        setAiError(null);
        sendMessage(content);
      } else {
        // Clear suggestions if content is empty
        setAiSuggestions([]);
        setIsProcessingAI(false);
        setAiError(null);
      }
    }, 1000), // Increased debounce time to reduce API calls
    [sendMessage]
  );

  const handleEditorChange = (content: string) => {
    onContentChange(content);
    // Only send to AI if we have substantial content
    if (content.length > 50) {
      // Minimum content threshold
      sendEditorContent(content);
    } else {
      // Clear suggestions for minimal content
      setAiSuggestions([]);
      setIsProcessingAI(false);
      setAiError(null);
    }
  };
  // ===== END TASK 2 =====

  return (
    <div className="flex w-full h-full">
      {/* Main editor area */}
      <div className="flex-1 h-full overflow-y-auto">
        <Editor handleEditorChange={handleEditorChange} content={content} />
      </div>

      {/* ===== TASK 2: REAL-TIME AI SUGGESTIONS - AI Suggestions Sidebar ===== */}
      <SuggestionsSidebar
        suggestions={aiSuggestions}
        isProcessing={isProcessingAI}
        error={aiError}
      />
      {/* ===== END TASK 2 ===== */}
    </div>
  );
}
// ===== END TASK 2 =====
