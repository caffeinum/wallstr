"use client";
import {useState, useRef, useEffect} from "react";
import { STORAGE_KEYS } from "@/hooks/useLocalStorage";

export default function ChatInput() {
  const [message, setMessage] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(STORAGE_KEYS.DRAFT_MESSAGE) || "";
    }
    return "";
  });
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize logic
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    const lineHeight = parseInt(getComputedStyle(textarea).lineHeight);
    const maxHeight = lineHeight * 5;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);

    textarea.style.height = `${newHeight}px`;
  }, [message]);

  // Save to localStorage on input
  useEffect(() => {
    if (message.trim()) {
      localStorage.setItem(STORAGE_KEYS.DRAFT_MESSAGE, message);
    } else {
      localStorage.removeItem(STORAGE_KEYS.DRAFT_MESSAGE);
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    console.log("Sending message:", message);
    setMessage("");
    localStorage.removeItem(STORAGE_KEYS.DRAFT_MESSAGE);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Submit on Ctrl+Enter or Cmd+Enter (for Mac)
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="p-4">
      <form onSubmit={handleSubmit} className="mx-auto max-w-4xl relative">
        <div className="relative flex items-start">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Ctrl+Enter to send)"
            rows={1}
            className="textarea textarea-bordered w-full pr-20 resize-none min-h-[2.5rem] max-h-[10rem] overflow-y-auto"
          />
          <div className="absolute right-0 top-1/2 -translate-y-1/2">
            <button
              type="submit"
              className="btn btn-ghost cursor-pointer hover:bg-transparent hover:border-0 hover:shadow-none border-0 active:bg-transparent active:border-0"
              disabled={!message.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
