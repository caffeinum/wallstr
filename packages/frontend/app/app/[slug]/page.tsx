"use client";
import { useParams } from "next/navigation";
import { InfiniteData, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import PDFViewer from "@/components/pdf_viewer/PDFViewer";
import ChatInput from "@/components/chat/ChatInput";
import ChatMessages from "@/components/chat/ChatMessages";
import ChatsList from "@/components/chat/ChatsList";
import { api } from "@/api";
import { getDocumentType } from "@/components/chat/utils";
import type { DocumentPayload, GetChatMessagesResponse } from "@/api/wallstr-sdk";

type TDocument = {
  documentUrl: string;
  page: number;
};

export default function ChatPage() {
  const { slug } = useParams<{ slug: string }>();
  const queryClient = useQueryClient();
  const [selectedDocument, setSelectedDocument] = useState<TDocument | null>(null);

  const { mutate, isPending } = useMutation({
    mutationFn: async ({ message, attachedFiles }: { message: string; attachedFiles: File[] }) => {
      const { data } = await api.chat.sendChatMessage({
        path: { slug },
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

      const pendingDocuments = data.pending_documents || [];
      Promise.all(
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
      );

      return data;
    },
    onMutate: async ({ message, attachedFiles }) => {
      await queryClient.cancelQueries({ queryKey: ["/chat", slug] });

      const previousMessages = queryClient.getQueryData(["/chat", slug]);

      const optimisticMessage = {
        id: `temp-${Date.now()}`,
        content: message,
        role: "user",
        documents: attachedFiles.map((file) => ({
          id: `temp-${file.name}`,
          filename: file.name,
          status: "uploading",
        })),
      };

      queryClient.setQueryData(["/chat", slug], (old: InfiniteData<GetChatMessagesResponse>) => ({
        pages: [
          {
            items: [optimisticMessage],
            cursor: null,
          },
          ...(old?.pages || []),
        ],
        pageParams: [null, ...(old?.pageParams || [])],
      }));

      return { previousMessages };
    },
    onError: (_, __, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(["/chat", slug], context.previousMessages);
      }
    },
  });

  const handleRefClick = async (href: string) => {
    const { data } = await api.documents.getDocumentBySection({
      path: { section_id: href },
    });

    if (!data) return;
    setSelectedDocument({
      documentUrl: data.document_url,
      page: data.page_number,
    });
  };

  return (
    <div className="flex flex-col md:flex-row flex-1 bg-base-200">
      <ChatsList slug={slug} />
      <div className="flex flex-1 flex-col overflow-y-scroll">
        <ChatMessages slug={slug} className="flex-1 overflow-y-scroll" onRefClick={handleRefClick} />
        <ChatInput onSubmit={(message, files) => mutate({ message, attachedFiles: files })} isPending={isPending} />
      </div>
      {selectedDocument && (
        <div className="min-w-96 max-w-2xl bg-base-100 border-l border-base-300 flex flex-col">
          <PDFViewer {...selectedDocument} onClose={() => setSelectedDocument(null)} />
        </div>
      )}
    </div>
  );
}
