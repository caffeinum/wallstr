import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { twMerge } from "tailwind-merge";
import { useState, useEffect } from "react";
import { RiMenuUnfoldFill } from "react-icons/ri";
import { RiMenuUnfold2Fill } from "react-icons/ri";

import { api } from "@/api";

export default function ChatsList({
  slug,
  className,
  forceCollapse,
}: {
  slug?: string;
  className?: string;
  forceCollapse?: boolean;
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { data: chats } = useQuery({
    queryKey: ["/chats"],
    queryFn: async () => {
      const { data } = await api.chat.listChats({ throwOnError: true });
      return data;
    },
  });

  useEffect(() => {
    if (forceCollapse) {
      setIsCollapsed(forceCollapse);
    }
  }, [forceCollapse]);

  if (!chats) return null;

  return (
    <div
      className={twMerge(
        "relative py-4 px-2 transition-all duration-300",
        className,
        isCollapsed ? "md:w-12" : "md:w-48",
      )}
    >
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="cursor-pointer md:absolute left-3 top-4 p-2 hover:bg-base-300 rounded-lg transition-colors"
        aria-label={isCollapsed ? "Expand chat list" : "Collapse chat list"}
      >
        {isCollapsed ? (
          <RiMenuUnfoldFill size={18} className="text-base-content/60" />
        ) : (
          <RiMenuUnfold2Fill size={18} className="text-base-content/60" />
        )}
      </button>
      <div className={`md:flex md:flex-col gap-2 md:mt-10 ${isCollapsed ? "hidden md:hidden" : ""}`}>
        <Link
          href="/app"
          className={`badge badge-md ${!slug ? "badge-neutral" : "badge-ghost"} transition-colors cursor-pointer whitespace-nowrap`}
        >
          New chat...
        </Link>
        {chats.items.map((chat) => (
          <Link
            key={chat.id}
            href={`/app/${chat.slug}`}
            className={`badge badge-md ${
              chat.slug === slug ? "badge-neutral" : "badge-ghost"
            } transition-colors cursor-pointer whitespace-nowrap`}
          >
            {chat.title || chat.slug}
          </Link>
        ))}
      </div>
    </div>
  );
}
