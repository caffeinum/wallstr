"use client";
import { useEffect, useRef, useState } from "react";
import { InfiniteData, useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { FaFile, FaFileImage, FaFilePdf, FaFileWord, FaFileExcel } from "react-icons/fa";
import { format } from "date-fns";
import { twMerge } from "tailwind-merge";

import { api } from "@/api";
import { settings } from "@/conf";
import type { ChatMessageRole, GetChatMessagesResponse } from "@/api/wallstr-sdk/types.gen";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface DocumentIconProps {
  filename: string;
}

function DocumentIcon({ filename }: DocumentIconProps) {
  const ext = filename.split(".").pop()?.toLowerCase();

  switch (ext) {
    case "pdf":
      return <FaFilePdf className="w-4 h-4" />;
    case "doc":
    case "docx":
      return <FaFileWord className="w-4 h-4" />;
    case "xls":
    case "xlsx":
      return <FaFileExcel className="w-4 h-4" />;
    case "jpg":
    case "jpeg":
    case "png":
    case "gif":
      return <FaFileImage className="w-4 h-4" />;
    default:
      return <FaFile className="w-4 h-4" />;
  }
}

interface StreamingMessage {
  id: string;
  content: string;
  loading?: boolean;
}

export default function ChatMessages({
  slug,
  className,
  onRefClick,
}: {
  slug?: string;
  className?: string;
  onRefClick: (href: string) => void;
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamingMessages, setStreamingMessages] = useState<StreamingMessage[]>([]);
  const queryClient = useQueryClient();

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useInfiniteQuery({
    queryKey: ["/chat", slug],
    queryFn: async ({ pageParam }) => {
      const { data } = await api.chat.getChatMessages({
        path: { slug: slug as string },
        query: { cursor: pageParam },
        throwOnError: true,
      });
      return data;
    },
    getNextPageParam: (lastPage) => lastPage?.cursor,
    initialPageParam: 0,
    enabled: !!slug,
  });

  useEffect(() => {
    if (!slug) return;
    console.log("Connecting to SSE");

    const eventSource = new EventSource(`${settings.API_URL}/chats/${slug}/messages/stream`, {
      withCredentials: true,
    });

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "message_start":
          setStreamingMessages((streamingMessages) => [
            ...streamingMessages,
            { id: data.id, content: "", loading: true },
          ]);
          break;
        case "message":
          setStreamingMessages((streamingMessages) => {
            const index = streamingMessages.findIndex((message) => message.id === data.id);
            if (index === -1) return streamingMessages;

            return [
              ...streamingMessages.slice(0, index),
              { id: data.id, content: streamingMessages[index].content + data.content },
              ...streamingMessages.slice(index + 1),
            ];
          });
          break;
        case "message_end":
          setStreamingMessages((streamingMessages) => {
            const index = streamingMessages.findIndex((message) => message.id === data.id);
            if (index === -1) return streamingMessages;

            return [...streamingMessages.slice(0, index), ...streamingMessages.slice(index + 1)];
          });

          // Update the cache with the completed message using the new ID
          queryClient.setQueryData<InfiniteData<GetChatMessagesResponse>>(["/chat", slug], (old) => {
            if (!old) return old;

            const completedMessage = {
              id: data.new_id,
              content: data.content,
              role: "assistant" as ChatMessageRole,
              created_at: data.created_at,
              documents: [],
            };

            return {
              pages: [
                {
                  items: [completedMessage, ...old.pages[0].items],
                  cursor: old.pages[0].cursor,
                },
                ...old.pages.splice(1),
              ],
              pageParams: old.pageParams,
            };
          });

          break;
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE Error:", error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [slug, queryClient]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [streamingMessages, data?.pages]);

  const MarkdownComponents = {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    a: ({ children, href, ...props }: any) => {
      if (!href) return null;
      return (
        <span onClick={() => onRefClick(href)} className="link" {...props}>
          {children}
        </span>
      );
    },
  };

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-4xl">
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-base-300"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const messages = data?.pages.flatMap((page) => page?.items).reverse() ?? [];

  return (
    <div className={twMerge("flex flex-col justify-end py-4", className)}>
      <div className="overflow-y-scroll max-w-4xl w-full mx-auto">
        <div className="space-y-4 w-full pr-4">
          {hasNextPage && (
            <button
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              className="btn btn-ghost btn-sm w-full"
            >
              {isFetchingNextPage ? "Loading more..." : "Load more"}
            </button>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`chat ${message.role === "user" ? "chat-end" : "chat-start"}`}>
              {message.documents && message.documents.length > 0 && (
                <div className="chat-header max-w-full truncate">
                  <div className="w-full">
                    {message.documents.map((doc) => (
                      <button
                        key={doc.id}
                        onClick={() => console.log(doc)}
                        className="flex items-center gap-2 py-2 hover:bg-base-200 px-2 rounded w-full text-left"
                      >
                        <DocumentIcon filename={doc.filename} />
                        <span className="text-sm truncate">{doc.filename}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {message.content && (
                <>
                  <div
                    className={`chat-bubble prose prose-sm ${
                      message.role === "user" ? "bg-neutral text-neutral-content whitespace-pre-wrap" : ""
                    }`}
                  >
                    <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                      {message.content}
                    </Markdown>
                  </div>

                  {message.created_at && (
                    <div className="chat-footer opacity-50 mt-0.5">{format(new Date(message.created_at), "p")}</div>
                  )}
                </>
              )}
            </div>
          ))}

          {streamingMessages.map((message) => (
            <div className="chat chat-start" key={message.id}>
              <div className="chat-bubble prose prose-sm">
                <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                  {message.loading ? "..." : message.content}
                </Markdown>
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}
