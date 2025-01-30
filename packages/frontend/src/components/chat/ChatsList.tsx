import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/api";

export default function ChatsList({ slug }: { slug?: string }) {
  const { data: chats } = useQuery({
    queryKey: ["/chats"],
    queryFn: async () => {
      const { data } = await api.chat.listChats({ throwOnError: true });
      return data;
    },
  });

  if (!chats) return null;

  return (
    <div className="gap-2 p-4 overflow-x-auto">
      <div className="mx-auto max-w-4xl">
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
