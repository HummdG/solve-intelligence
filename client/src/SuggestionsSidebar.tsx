// ===== TASK 2: REAL-TIME AI SUGGESTIONS - Suggestions Sidebar Component =====
// File: client/src/SuggestionsSidebar.tsx
import { FC } from "react";
import styled from "@emotion/styled";

// TypeScript interfaces for AI suggestions
export interface AISuggestion {
  type: string;
  severity: "high" | "medium" | "low";
  paragraph: number;
  description: string;
  suggestion: string;
}

export interface SuggestionsData {
  issues: AISuggestion[];
}

export interface WebSocketMessage {
  type: "suggestions" | "status" | "error";
  data: SuggestionsData | { message: string };
  status: "success" | "processing" | "error";
}

interface SuggestionsSidebarProps {
  suggestions: AISuggestion[];
  isProcessing: boolean;
  error: string | null;
}

const SidebarContainer = styled.div`
  width: 300px;
  height: 100%;
  background: #f8f9fa;
  border-left: 1px solid #e9ecef;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
`;

const SidebarHeader = styled.h3`
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 8px;
`;

interface StatusIndicatorProps {
  isProcessing: boolean;
}

interface SeverityProps {
  severity: "high" | "medium" | "low";
}

const StatusIndicator = styled.div<StatusIndicatorProps>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: ${(props: StatusIndicatorProps) =>
    props.isProcessing ? "#ffc107" : "#28a745"};
  animation: ${(props: StatusIndicatorProps) =>
    props.isProcessing ? "pulse 1.5s infinite" : "none"};

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
    100% {
      opacity: 1;
    }
  }
`;

const SuggestionCard = styled.div<SeverityProps>`
  background: white;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border-left: 4px solid
    ${(props: SeverityProps) =>
      props.severity === "high"
        ? "#dc3545"
        : props.severity === "medium"
        ? "#ffc107"
        : "#28a745"};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const SuggestionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
`;

const SuggestionType = styled.span`
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #6c757d;
`;

const SeverityBadge = styled.span<SeverityProps>`
  background-color: ${(props: SeverityProps) =>
    props.severity === "high"
      ? "#dc3545"
      : props.severity === "medium"
      ? "#ffc107"
      : "#28a745"};
  color: ${(props: SeverityProps) =>
    props.severity === "medium" ? "#000" : "#fff"};
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
`;

const ParagraphNumber = styled.div`
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 4px;
`;

const Description = styled.p`
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #495057;
  line-height: 1.4;
`;

const Suggestion = styled.p`
  margin: 0;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 13px;
  color: #495057;
  font-style: italic;
  line-height: 1.4;
`;

const EmptyState = styled.div`
  text-align: center;
  color: #6c757d;
  padding: 32px 16px;
  font-style: italic;
`;

const ErrorMessage = styled.div`
  background: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
`;

const ProcessingMessage = styled.div`
  background: #fff3cd;
  color: #856404;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const SuggestionsSidebar: FC<SuggestionsSidebarProps> = ({
  suggestions,
  isProcessing,
  error,
}) => {
  return (
    <SidebarContainer>
      <SidebarHeader>
        <StatusIndicator isProcessing={isProcessing} />
        AI Suggestions
      </SidebarHeader>

      {error && <ErrorMessage>⚠️ {error}</ErrorMessage>}

      {isProcessing && (
        <ProcessingMessage>
          <span>🔄</span>
          Analyzing document for suggestions...
        </ProcessingMessage>
      )}

      {!isProcessing && suggestions.length === 0 && !error && (
        <EmptyState>
          💡 AI suggestions will appear here as you edit your document.
        </EmptyState>
      )}

      {suggestions.map((suggestion: AISuggestion, index: number) => (
        <SuggestionCard key={index} severity={suggestion.severity}>
          <SuggestionHeader>
            <SuggestionType>{suggestion.type}</SuggestionType>
            <SeverityBadge severity={suggestion.severity}>
              {suggestion.severity}
            </SeverityBadge>
          </SuggestionHeader>

          <ParagraphNumber>📍 Paragraph {suggestion.paragraph}</ParagraphNumber>

          <Description>{suggestion.description}</Description>

          <Suggestion>💡 {suggestion.suggestion}</Suggestion>
        </SuggestionCard>
      ))}
    </SidebarContainer>
  );
};

export default SuggestionsSidebar;
// ===== END TASK 2 =====
