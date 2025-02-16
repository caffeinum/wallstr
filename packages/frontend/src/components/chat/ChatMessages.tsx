"use client";
import { AnchorHTMLAttributes, useEffect, useMemo, useRef, useState } from "react";
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

type TReferencesMap = {
  [key: string]: number;
};

export default function ChatMessages({
  slug,
  className,
  onRefClick,
}: {
  slug?: string;
  className?: string;
  onRefClick: (id: string | null) => void;
}) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const firstLoadRef = useRef(true);
  const [streamingMessages, setStreamingMessages] = useState<StreamingMessage[]>([]);
  const [referencesMap, setReferencesMap] = useState<TReferencesMap>({});
  const [selectedRef, selectRef] = useState<string | null>(null);
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

  const messages = useMemo(() => data?.pages.flatMap((page) => page?.items).reverse() ?? [], [data]);
  // parse content and find references
  useEffect(() => {
    if (!messages.length) return;

    const newRefs: TReferencesMap = { ...referencesMap };
    let nextIndex = Object.keys(referencesMap).length + 1;
    let hasChanges = false;

    messages.forEach((message) => {
      const matches = message.content.match(/\[([^\]]+)\]\(([^)]+)\)/g);
      if (!matches) return;

      matches.forEach((match) => {
        const href = match.match(/\(([^)]+)\)/)?.[1];
        if (!href) return;

        const ids = href.split(",").map((id) => id.trim());
        ids.forEach((id) => {
          if (!newRefs[id]) {
            newRefs[id] = nextIndex++;
            hasChanges = true;
          }
        });
      });
    });
    if (hasChanges) {
      setReferencesMap(newRefs);
    }
  }, [messages, referencesMap, setReferencesMap]);

  const scrollToBottom = (mode: "smooth" | "instant") => {
    messagesEndRef.current?.scrollIntoView({ behavior: mode });
  };

  useEffect(() => {
    // Only scroll on first load of messages or when there are streaming messages
    if (firstLoadRef.current && messages.length > 0) {
      scrollToBottom("instant");
      firstLoadRef.current = false;
    } else {
      scrollToBottom("smooth");
    }
  }, [streamingMessages, messages]);

  const MarkdownComponents = {
    a: ({ href }: AnchorHTMLAttributes<HTMLAnchorElement>) => (
      <ReferenceLink
        href={href}
        onRefClick={(id: string | null) => {
          if (id === selectedRef) {
            id = null;
          }
          onRefClick(id);
          selectRef(id);
        }}
        referencesMap={referencesMap}
        selectedId={selectedRef}
      />
    ),
  };

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto max-w-4xl flex flex-col justify-end items-stretch h-full">
          <div className="animate-pulse space-y-4">
            <div className="chat chat-end">
              <div className="chat-bubble bg-neutral/20 text-neutral-content w-2/3 md:w-1/2 h-20"></div>
            </div>
            <div className="chat chat-start">
              <div className="chat-bubble w-full md:w-2/3 h-56"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

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

function ReferenceLink({
  href,
  onRefClick,
  referencesMap,
  selectedId,
}: {
  href?: string;
  onRefClick: (id: string) => void;
  referencesMap: TReferencesMap;
  selectedId: string | null;
}) {
  if (!href) return null;

  const ids = href.split(",").map((id: string) => id.trim());
  if (ids.length === 0) return null;

  return (
    <span className="inline-flex flex-wrap gap-1">
      {ids.map((id, i) => (
        <button
          key={`${id}-${i}`}
          onClick={() => onRefClick(id)}
          className={twMerge(
            "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
            "transition-colors duration-200 cursor-pointer",
            selectedId === id ? "bg-primary text-primary-content" : "bg-base-200 hover:bg-base-300",
          )}
        >
          <span className="font-medium">{referencesMap[id]}.</span>
        </button>
      ))}
    </span>
  );
}
