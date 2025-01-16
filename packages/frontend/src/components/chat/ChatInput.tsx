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
    <>
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

      <div className="my-4 text-center text-xs text-base-content/60">
        <a
          href="https://github.com/limanAI/dyvy"
          target="_blank"
          rel="noopener noreferrer"
          className="link link-hover inline-flex items-center gap-1"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="feather feather-star"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          Star us on GitHub
        </a>
      </div>
    </>
  );
}
