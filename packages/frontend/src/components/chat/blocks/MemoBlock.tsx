import { useCallback, useEffect, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import {
  ClientSideRowModelModule,
  ColDef,
  RowAutoHeightModule,
  themeAlpine,
  colorSchemeDarkBlue,
} from "ag-grid-community";
import Markdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { convert as htmlToText } from "html-to-text";
import { groupBy } from "es-toolkit";
import { useTheme } from "next-themes";
import { HiOutlineArrowsExpand } from "react-icons/hi";
import { HiOutlineArrowsPointingIn } from "react-icons/hi2";

import CopyButton from "./CopyButton";

import type { MouseEvent } from "react";
import type { MemoSection, ChatMessage } from "@/api/wallstr-sdk/types.gen";

export default function MemoBlock({
  message,
  MarkdownComponents,
  onToggleExpand,
  className,
}: {
  message: ChatMessage;
  MarkdownComponents: Components;
  onToggleExpand: (sExpanded: boolean) => void;
  className?: string;
}) {
  const { resolvedTheme } = useTheme();
  const sections = useMemo(() => groupBy(message.memo?.sections ?? [], (section) => section.group), [message]);
  const pages = useMemo(() => Object.keys(sections).sort(), [sections]);
  const [page, setPage] = useState(0);
  const [data, setData] = useState(sections[pages[page]]);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    setData(
      sections[pages[page]]?.map((section, index) => ({ ...section, value: { index, content: section.content } })),
    );
  }, [page, pages, sections]);

  const toggleExpand = useCallback(
    (e: MouseEvent<SVGElement>) => {
      e.preventDefault();
      e.stopPropagation();

      const _isExpanded = !isExpanded;
      onToggleExpand(_isExpanded);
      setIsExpanded(_isExpanded);
    },
    [onToggleExpand, setIsExpanded, isExpanded],
  );

  const columnDefs: ColDef<MemoSection>[] = useMemo(() => {
    const headerName = pages[page] || "";

    return [
      {
        headerName: "",
        field: "aspect",
        spanHeaderHeight: true,
        maxWidth: 180,
        wrapText: true,
      },
      {
        headerName: headerName,
        wrapText: true,
        autoHeight: true,
        flex: 1,
        editable: true,
        cellRenderer: ({ data }: { data: MemoSection }) => {
          return (
            <div className="prose prose-sm prose-stone">
              <div id={`memo-${message.id}-${data.index}`}>
                <Markdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                  {data.content}
                </Markdown>
              </div>

              <div className="text-right">
                <CopyButton
                  className="align-top"
                  onCopy={async () => {
                    let html = "";
                    const elem = document.getElementById(`memo-${message.id}-${data.index}`);
                    if (elem) {
                      html = elem.innerHTML.trim();
                      // remove all links to the documents sections
                      html = html.replace(/<button[^>]*>.*?<\/button>/g, "");
                    }
                    navigator.clipboard.write([
                      new ClipboardItem({
                        "text/html": new Blob([html], { type: "text/html" }),
                        "text/plain": new Blob([htmlToText(html)], { type: "text/plain" }),
                      }),
                    ]);
                  }}
                />
              </div>
            </div>
          );
        },
      },
    ];
  }, [pages, page, MarkdownComponents, message.id]);

  return (
    <div
      className={`${className || ""} flex flex-col ${isExpanded ? "absolute z-3 top-0 left-0 h-screen w-full bg-base-100" : "h-[calc(100vh-10em)]"}`}
    >
      <div className="relative flex-1">
        <div className="absolute top-2 right-2 p-2 z-2">
          {isExpanded ? (
            <HiOutlineArrowsPointingIn className="w-4 h-4 cursor-pointer animate-press" onClick={toggleExpand} />
          ) : (
            <HiOutlineArrowsExpand className="w-4 h-4 cursor-pointer animate-press" onClick={toggleExpand} />
          )}
        </div>

        <AgGridReact
          modules={[ClientSideRowModelModule, RowAutoHeightModule]}
          theme={resolvedTheme === "light" ? themeAlpine : themeAlpine.withPart(colorSchemeDarkBlue)}
          domLayout="normal"
          columnDefs={columnDefs}
          rowData={data}
        />
      </div>

      <div className="mt-2 relative flex justify-center">
        <ul className="steps text-xs">
          {Array.from({ length: pages.length }, (_, index) => (
            <li
              key={index}
              className={`step cursor-pointer ${page === index ? "step-neutral" : ""}`}
              onClick={() => setPage(index)}
            ></li>
          ))}
          {/* TOOD: switch from steps to dots
          {Array.from({ length: pages.length }, (_, index) => (
            <li
              key={index}
              className={`cursor-pointer rounded-full w-7 h-7 flex items-center justify-center
                ${page === index ? "inset-shadow-sm border-1 border-base-content/20" : "text-base-content/70"}`}
              onClick={() => setPage(index)}
            >
              {index + 1}
            </li>
          ))}
          */}
        </ul>
      </div>
    </div>
  );
}
