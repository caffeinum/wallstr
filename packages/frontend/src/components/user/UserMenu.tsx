"use client";
import { useCallback } from "react";
import { useRouter } from "next/navigation";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/api";

export default function UserMenu() {
  const router = useRouter();

  const { isPending, isError, data, error } = useQuery({
    queryKey: ["/auth/me"],
    queryFn: async () => {
      const { data } = await api.auth.getCurrentUser({ throwOnError: true });
      return data;
    },
  });

  const handleSignOut = useCallback(() => {
    router.push("/auth/signout");
  }, [router]);

  if (isPending) {
    return <div className="animate-pulse h-8 w-8 rounded-full bg-gray-200" />;
  }

  if (isError) {
    console.error("Error fetching user:", error);
  }

  return (
    <div className="dropdown dropdown-end">
      <div tabIndex={0} role="button" className="avatar avatar-placeholder btn btn-ghost btn-circle">
        <div className="w-10 rounded-full bg-neutral text-neutral-content">
          <span className="text-lg font-semibold">{data?.username?.[0]?.toUpperCase() ?? "?"}</span>
        </div>
      </div>
      <ul tabIndex={0} className="dropdown-content menu menu-sm z-[1] mt-3 w-52 rounded-box bg-base-100 p-2 shadow">
        <li className="menu-title px-4 py-2">
          <span className="text-xs font-semibold uppercase text-base-content/80">Signed in as</span>
          <span className="text-sm font-medium">{data?.email}</span>
        </li>
        <div className="divider my-0" />
        <li>
          <button onClick={handleSignOut}>Sign out</button>
        </li>
      </ul>
    </div>
  );
}
