"use client";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";

import ChatInput from "@/components/chat/ChatInput";
import ChatMessages from "@/components/chat/ChatMessages";
import ChatsList from "@/components/chat/ChatsList";

export default function ChatPage() {
  const { slug } = useParams<{ slug: string }>();

  const { mutate, isPending } = useMutation({
    mutationFn: async ({ message, attachedFiles }: { message: string; attachedFiles: File[] }) => {
      // TODO: Implement sending message in existing chat
      console.log("Sending message:", message, attachedFiles);
    },
  });

  return (
    <div className="flex flex-col grow">
      <main className="flex-1 overflow-hidden bg-base-200">
        <div className="flex h-full flex-col">
          <ChatsList slug={slug} />
          <ChatMessages slug={slug} />
          <ChatInput onSubmit={(message, files) => mutate({ message, attachedFiles: files })} isPending={isPending} />
        </div>
      </main>
    </div>
  );
}
