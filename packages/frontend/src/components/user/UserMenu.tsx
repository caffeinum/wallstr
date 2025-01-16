"use client";
import {useCallback, useEffect, useState} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import { clearLocalStorage } from "@/hooks/useLocalStorage";

interface UserData {
  username: string;
  email: string;
}

export default function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          router.push("/auth/signin");
          return;
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch user");
        }

        const userData = await response.json();
        setUser(userData);
      } catch (error) {
        console.error("Error fetching user:", error);
        router.push("/auth/signin");
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [router]);

  const handleSignOut = useCallback(async () => {
    try {
      const token = sessionStorage.getItem("access_token");
      if (token) {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } finally {
      sessionStorage.removeItem("access_token");
      clearLocalStorage();
      router.push("/auth/signin");
    }
  }, [router]);

  if (isLoading) {
    return <div className="animate-pulse h-8 w-8 rounded-full bg-gray-200" />;
  }

  return (
    <div className="dropdown dropdown-end">
      <div tabIndex={0} role="button" className="avatar avatar-placeholder btn btn-ghost btn-circle">
        <div className="w-10 rounded-full bg-neutral text-neutral-content">
          <span className="text-lg font-semibold">{user?.username?.[0]?.toUpperCase() ?? "?"}</span>
        </div>
      </div>
      <ul tabIndex={0} className="dropdown-content menu menu-sm z-[1] mt-3 w-52 rounded-box bg-base-100 p-2 shadow">
        <li className="menu-title px-4 py-2">
          <span className="text-xs font-semibold uppercase text-base-content/80">Signed in as</span>
          <span className="text-sm font-medium">{user?.email}</span>
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
