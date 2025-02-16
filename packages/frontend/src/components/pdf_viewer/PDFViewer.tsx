"use client";
import { useState, useEffect, useMemo } from "react";
import { FaTimes } from "react-icons/fa";
import { Document, Page, pdfjs } from "react-pdf";
import { debounce } from "es-toolkit";

// Initialize PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({
  documentUrl,
  width,
  page,
  onClose,
}: {
  documentUrl: string;
  width: number;
  page: number;
  onClose: () => void;
}) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [debouncedWidth, setDebouncedWidth] = useState(width);

  const debouncedSetWidth = useMemo(() => debounce((value: number) => setDebouncedWidth(value), 100), []);
  useEffect(() => {
    debouncedSetWidth(width);
    return () => {
      debouncedSetWidth.cancel();
    };
  }, [width, debouncedSetWidth]);

  const onLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(page);
  };

  return (
    <>
      <div className="flex justify-between items-center p-4 border-b border-base-300">
        <h3 className="text-lg font-semibold truncate">Document</h3>
        <div className="flex items-center gap-2">
          <button onClick={onClose} className="btn btn-ghost btn-sm btn-square">
            <FaTimes />
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4" style={{ width: width + 2 }}>
        <Document file={documentUrl} onLoadSuccess={onLoadSuccess} className="flex flex-col items-center">
          <Page pageNumber={pageNumber} width={debouncedWidth} renderTextLayer={true} renderAnnotationLayer={true} />
        </Document>
      </div>
      <div className="p-4 border-t border-base-300 flex justify-between items-center">
        <span className="text-sm">
          Page {pageNumber} of {numPages}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
            disabled={pageNumber <= 1}
            className="btn btn-ghost btn-sm"
          >
            Previous
          </button>
          <button
            onClick={() => setPageNumber((prev) => Math.min(prev + 1, numPages || 1))}
            disabled={pageNumber >= (numPages || 1)}
            className="btn btn-ghost btn-sm"
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}
