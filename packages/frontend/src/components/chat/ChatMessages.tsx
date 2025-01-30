"use client";
import { useEffect, useRef } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { FaFile, FaFileImage, FaFilePdf, FaFileWord, FaFileExcel } from "react-icons/fa";

import { api } from "@/api";

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

export default function ChatMessages({ slug }: { slug?: string }) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, []);

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

  const messages = data?.pages.flatMap((page) => page?.items) ?? [];

  return (
    <div className="flex-1 flex flex-col justify-end overflow-y-auto p-4">
      <div className="mx-auto max-w-4xl space-y-4 w-full">
        {hasNextPage && (
          <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage} className="btn btn-ghost btn-sm w-full">
            {isFetchingNextPage ? "Loading more..." : "Load more"}
          </button>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`chat ${message.role === "user" ? "chat-end" : "chat-start"}`}>
            {message.documents && message.documents.length > 0 && (
              <div className="chat-header">
                <div>
                  {message.documents.map((doc) => (
                    <div key={doc.id} className="flex items-center gap-2 py-2">
                      <DocumentIcon filename={doc.filename} />
                      <span className="text-sm">{doc.filename}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {message.content && (
              <div
                className={`chat-bubble whitespace-pre ${message.role === "user" ? "bg-neutral text-neutral-content" : ""}`}
              >
                {message.content}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
