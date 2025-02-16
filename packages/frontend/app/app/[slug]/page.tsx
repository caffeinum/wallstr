"use client";
import { useParams } from "next/navigation";
import { InfiniteData, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useCallback, useRef, useEffect } from "react";
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

const MIN_PANEL_WIDTH = 576; // w-xl
const MAX_PANEL_WIDTH = 896; // max-w-4xl
const MD_BREAKPOINT = 768; // md breakpoint in pixels
const CHATS_LIST_COLLAPSE_WIDTH = 700;

export default function ChatPage() {
  const { slug } = useParams<{ slug: string }>();
  const queryClient = useQueryClient();
  const [selectedDocument, setSelectedDocument] = useState<TDocument | null>(null);
  const [isMdScreen, setIsMdScreen] = useState(false);
  const [panelWidth, setPanelWidth] = useState(MIN_PANEL_WIDTH);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  // Handle screen size changes
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMdScreen(window.innerWidth >= MD_BREAKPOINT);
      // Reset panel width when switching to mobile
      if (window.innerWidth < MD_BREAKPOINT) {
        setPanelWidth(MIN_PANEL_WIDTH);
      } else {
        setPanelWidth(Math.min(Math.max(MIN_PANEL_WIDTH, window.innerWidth / 2), MAX_PANEL_WIDTH));
      }
    };

    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!isMdScreen) return;
      isDragging.current = true;
      startX.current = e.pageX;
      startWidth.current = panelWidth;
      document.body.style.cursor = "col-resize";
      e.preventDefault();
    },
    [panelWidth, isMdScreen],
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging.current || !isMdScreen) return;

      const delta = startX.current - e.pageX;
      const newWidth = Math.min(Math.max(startWidth.current + delta, MIN_PANEL_WIDTH), MAX_PANEL_WIDTH);
      setPanelWidth(newWidth);
    },
    [isMdScreen],
  );

  const handleMouseUp = useCallback(() => {
    if (!isMdScreen) return;
    isDragging.current = false;
    document.body.style.cursor = "default";
  }, [isMdScreen]);

  useEffect(() => {
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

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
    <div className="flex flex-col md:flex-row flex-1 bg-base-200 w-full">
      <ChatsList slug={slug} forceCollapse={!!selectedDocument && panelWidth > CHATS_LIST_COLLAPSE_WIDTH} />
      <div className="flex flex-1 flex-col overflow-y-scroll">
        <ChatMessages slug={slug} className="flex-1 overflow-y-scroll" onRefClick={handleRefClick} />
        <ChatInput onSubmit={(message, files) => mutate({ message, attachedFiles: files })} isPending={isPending} />
      </div>
      {selectedDocument && (
        <div className="flex flex-row">
          <div
            className="hidden md:block w-1 hover:bg-base-300 cursor-col-resize active:bg-base-300 flex-shrink-0"
            onMouseDown={handleMouseDown}
          />
          <div className="bg-base-100 border-l border-base-300 flex flex-col w-full">
            <PDFViewer {...selectedDocument} onClose={() => setSelectedDocument(null)} width={panelWidth} />
          </div>
        </div>
      )}
    </div>
  );
}
