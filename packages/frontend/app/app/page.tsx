"use client";
import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useMutation } from "@tanstack/react-query";

import ChatInput from "@/components/chat/ChatInput";
import ChatMessages from "@/components/chat/ChatMessages";
import UserMenu from "@/components/user/UserMenu";
import { api } from "@/api";

export default function AppPage() {
  const router = useRouter();

  const { mutate, isPending } = useMutation({
    mutationFn: async ({ message, hasAttachments }: { message: string | null; hasAttachments: boolean }) => {
      const { data } = await api.chat.createChat({
        body: {
          message,
          has_attachments: hasAttachments,
        },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: (data) => {
      router.push(`/app/${data.slug}`);
    },
  });

  const createChat = useCallback(
    async (message: string, attachedFiles: File[]) => {
      mutate({
        message: message.trim() || null,
        hasAttachments: attachedFiles.length > 0,
      });
    },
    [mutate],
  );

  return (
    <div className="flex flex-col grow">
      <header className="border-b border-base-300 bg-base-100">
        <div className="flex h-16 items-center justify-between px-4">
          <h1 className="text-xl font-semibold">WallStr.chat</h1>
          <UserMenu />
        </div>
      </header>

      <main className="flex-1 overflow-hidden bg-base-200">
        <div className="flex h-full flex-col">
          <ChatMessages />
          <ChatInput onSubmit={createChat} isPending={isPending} />
        </div>
      </main>
    </div>
  );
}
