import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { twMerge } from "tailwind-merge";

import { api } from "@/api";

export default function ChatsList({ slug, className }: { slug?: string; className?: string }) {
  const { data: chats } = useQuery({
    queryKey: ["/chats"],
    queryFn: async () => {
      const { data } = await api.chat.listChats({ throwOnError: true });
      return data;
    },
  });

  if (!chats) return null;

  return (
    <div className={twMerge("py-4 px-2", className)}>
      <div className="md:flex md:flex-col gap-2 md:mt-10">
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
