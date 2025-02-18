import { useCallback } from "react";
import { HiMiniExclamationCircle } from "react-icons/hi2";
import { FaFile, FaFileImage, FaFilePdf, FaFileWord, FaFileExcel } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { throttle } from "es-toolkit";

import { api } from "@/api";
import type { Document, DocumentStatus } from "@/api/wallstr-sdk";

export default function DocumentsInlineBlock({
  documents,
  className,
  onDocumentOpen,
}: {
  documents: Document[];
  className?: string;
  onDocumentOpen?: (id: string) => void;
}) {
  const onRestartProcessing = throttle(
    async (id: string) =>
      api.documents.triggerProcessing({
        path: { document_id: id },
      }),
    1000,
  );

  if (!documents || documents.length === 0) {
    return null;
  }

  return (
    <div className={twMerge("chat-header max-w-full", className)}>
      <div>
        {documents.map((doc) => (
          <InlineDocument key={doc.id} {...doc} onOpen={onDocumentOpen} onRestartProcessing={onRestartProcessing} />
        ))}
      </div>
    </div>
  );
}

function InlineDocument({
  id,
  status,
  filename,
  onRestartProcessing,
  onOpen,
  error,
}: {
  id: string;
  status: DocumentStatus;
  filename: string;
  onRestartProcessing: (id: string) => void;
  onOpen?: (id: string) => void;
  error?: string | null;
}) {
  const onClick = useCallback(() => {
    if (status === "uploaded") return;
    if (!onOpen) return;

    onOpen(id);
  }, [onOpen, id, status]);

  return (
    <span className="flex items-center justify-end gap-2 p-2">
      <DocumentStatusIcon status={status} hasError={!!error} onRestartProcessing={() => onRestartProcessing(id)} />
      <DocumentIcon filename={filename} />
      <span
        className={`text-sm min-w-0 truncate max-w-42 sm:max-w-92 md:max-w-full ${status === "uploading" ? "" : "hover:link"}`}
        onClick={onClick}
      >
        <span>{filename}</span>
      </span>
    </span>
  );
}

function DocumentStatusIcon({
  status,
  hasError,
  onRestartProcessing,
}: {
  status: DocumentStatus;
  hasError?: boolean;
  onRestartProcessing: () => void;
}) {
  if (hasError) {
    return (
      <span className="tooltip" data-tip="Failed. Click to restart" onClick={onRestartProcessing}>
        <HiMiniExclamationCircle className="text-error w-4 h-4 cursor-pointer" />
      </span>
    );
  }
  switch (status) {
    case "uploading":
      return (
        <span className="tooltip" data-tip="Uploading">
          <span className="loading loading-spinner loading-xs text-base-content/30"></span>
        </span>
      );
    case "uploaded":
      return (
        <span className="tooltip" data-tip="In queue">
          <span className="loading loading-spinner loading-xs text-base-content/30"></span>
        </span>
      );
    case "processing":
      return (
        <span className="tooltip" data-tip="Processing">
          <span className="loading loading-bars loading-xs text-base-content/30"></span>
        </span>
      );
    case "ready":
    default:
      return null;
  }
}

function DocumentIcon({ filename }: { filename: string }) {
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
