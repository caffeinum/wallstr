"use client";
import {useState} from "react";

export default function ChatInput() {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    // TODO: Handle message submission
    console.log("Sending message:", message);
    setMessage("");
  };

  return (
    <div className="border-t border-base-300 bg-base-100 p-4">
      <form onSubmit={handleSubmit} className="mx-auto max-w-4xl relative">
        <div className="relative flex items-center">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="input input-bordered w-full pr-20"
          />
          <button type="submit" className="btn btn-ghost absolute right-0 cursor-pointer" disabled={!message.trim()}>
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
