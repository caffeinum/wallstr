import { useEffect, useMemo, useState } from "react";
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

import { MemoSection, ChatMessage } from "@/api/wallstr-sdk/types.gen";
import CopyButton from "../CopyButton";

type MemoBlockProps = {
  message: ChatMessage;
  MarkdownComponents: Components;
};

export default function MemoBlock({ message, MarkdownComponents }: MemoBlockProps) {
  const { resolvedTheme } = useTheme();
  const sections = useMemo(() => groupBy(message.memo?.sections ?? [], (section) => section.group), [message]);
  const pages = useMemo(() => Object.keys(sections).sort(), [sections]);
  const [page, setPage] = useState(0);
  const [data, setData] = useState(sections[pages[page]]);

  useEffect(() => {
    setData(
      sections[pages[page]]?.map((section, index) => ({ ...section, value: { index, content: section.content } })),
    );
  }, [page, pages, sections]);

  const columnDefs: ColDef<MemoSection>[] = useMemo(() => {
    const headerName = pages[page] || "";

    return [
      {
        headerName: "",
        field: "aspect",
        spanHeaderHeight: true,
        maxWidth: 180,
        minWidth: 50,
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
    <div>
      <div className="relative h-[calc(100vh-13em)]">
        <AgGridReact
          modules={[ClientSideRowModelModule, RowAutoHeightModule]}
          theme={resolvedTheme === "light" ? themeAlpine : themeAlpine.withPart(colorSchemeDarkBlue)}
          domLayout="normal"
          columnDefs={columnDefs}
          rowData={data}
        />
      </div>

      <div className="mt-2 relative z-100 flex justify-center">
        <ul className="steps text-xs">
          {Array.from({ length: pages.length }, (_, index) => (
            <li
              key={index}
              className={`step cursor-pointer ${page === index ? "step-neutral" : ""}`}
              onClick={() => setPage(index)}
            ></li>
          ))}
        </ul>
      </div>
    </div>
  );
}

