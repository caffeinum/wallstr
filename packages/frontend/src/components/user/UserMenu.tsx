"use client";
import {useCallback, useEffect, useState} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";

import {clearLocalStorage} from "@/hooks/useLocalStorage";

type TUser = {
  username: string;
  email: string;
};

export default function UserMenu() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const _token = localStorage.getItem("access_token");
    if (!_token) {
      router.push("/auth/signin");
      return;
    }
    setToken(_token);
  }, [router, setToken]);

  const {isPending, isError, data, error} = useQuery<TUser>({
    // eslint-disable-next-line @tanstack/query/exhaustive-deps
    queryKey: ["/auth/me"],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.["detail"] || JSON.stringify(data));
      }
      return data;
    },
    enabled: !!token,
  });

  const {mutate: signOut} = useMutation({
    mutationFn: async () => {
      const token = sessionStorage.getItem("access_token");
      if (token) {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    },
    onSettled: () => {
      sessionStorage.removeItem("access_token");
      clearLocalStorage();
      queryClient.clear();
      router.push("/auth/signin");
    },
  });

  const handleSignOut = useCallback(() => {
    signOut();
  }, [signOut]);

  if (isPending) {
    return <div className="animate-pulse h-8 w-8 rounded-full bg-gray-200" />;
  }

  if (isError) {
    console.error("Error fetching user:", error);
    router.push("/auth/signin");
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
          <Link href="/app/settings">Settings</Link>
        </li>
        <li>
          <button onClick={handleSignOut}>Sign out</button>
        </li>
      </ul>
    </div>
  );
}
