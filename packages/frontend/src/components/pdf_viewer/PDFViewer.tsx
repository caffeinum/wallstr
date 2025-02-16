"use client";
import { useState } from "react";
import { FaTimes } from "react-icons/fa";
import { Document, Page, pdfjs } from "react-pdf";

// Initialize PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PDFViewer({
  documentUrl,
  page,
  onClose,
}: {
  documentUrl: string;
  page: number;
  onClose: () => void;
}) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);

  const zoomIn = () => setScale((prev) => Math.min(prev + 0.1, 2.0));
  const zoomOut = () => setScale((prev) => Math.max(prev - 0.1, 0.5));

  const onLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(page);
  };

  return (
    <>
      <div className="flex justify-between items-center p-4 border-b border-base-300">
        <h3 className="text-lg font-semibold truncate">Document</h3>
        <div className="flex items-center gap-2">
          <button onClick={zoomOut} className="btn btn-ghost btn-sm">
            -
          </button>
          <span className="text-sm">{Math.round(scale * 100)}%</span>
          <button onClick={zoomIn} className="btn btn-ghost btn-sm">
            +
          </button>
          <button onClick={onClose} className="btn btn-ghost btn-sm btn-square">
            <FaTimes />
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <Document file={documentUrl} onLoadSuccess={onLoadSuccess} className="flex flex-col items-center">
          <Page
            pageNumber={pageNumber}
            scale={scale}
            className="mb-4"
            renderTextLayer={true}
            renderAnnotationLayer={true}
          />
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
