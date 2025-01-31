"use client";
import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useMutation } from "@tanstack/react-query";

import ChatInput from "@/components/chat/ChatInput";
import ChatMessages from "@/components/chat/ChatMessages";
import { api } from "@/api";

import type { DocumentPayload } from "@/api/wallstr-sdk";
import ChatsList from "@/components/chat/ChatsList";
import { getDocumentType } from "@/components/chat/utils";

export default function AppPage() {
  const router = useRouter();

  const { mutate, isPending } = useMutation({
    mutationFn: async ({ message, attachedFiles }: { message: string; attachedFiles: File[] }) => {
      const { data: chat } = await api.chat.createChat({
        body: {
          message: message.trim() || null,
          // TODO: generate sha-suffix for documents
          documents: attachedFiles.map(
            (f): DocumentPayload => ({
              filename: f.name,
              doc_type: getDocumentType(f),
            }),
          ),
        },
        throwOnError: true,
      });

      const pendingDocuments = chat.messages.items[0].pending_documents || [];
      Promise.all([
        pendingDocuments.map(async (document) => {
          const file = attachedFiles.find((file) => file.name === document.filename);
          if (!file) return;

          const response = await fetch(document.presigned_url, {
            method: "PUT",
            body: file,
          });

          if (response.ok) {
            await api.documents.markDocumentUploaded({ path: { id: document.id } });
          }
        }),
      ]);
      return chat;
    },
    onSuccess: (chat) => {
      router.push(`/app/${chat.slug}`);
    },
  });

  const createChat = useCallback(
    async (message: string, attachedFiles: File[]) => {
      mutate({
        message,
        attachedFiles,
      });
    },
    [mutate],
  );

  return (
    <div className="flex flex-col flex-1 bg-base-200">
      <ChatsList />
      <ChatMessages />
      <ChatInput onSubmit={createChat} isPending={isPending} />
    </div>
  );
}
