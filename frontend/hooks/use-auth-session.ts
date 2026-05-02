"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "../lib/api";
import type { User } from "../lib/types";

type UseAuthSessionOptions = {
  redirectToLogin?: boolean;
};

export function useAuthSession(options: UseAuthSessionOptions = {}) {
  const { redirectToLogin = false } = options;
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshUser() {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiFetch("/api/auth/me", {
        method: "GET",
        cache: "no-store",
      });

      if (response.status === 401) {
        setUser(null);
        if (redirectToLogin) {
          router.replace(`/login?next=${encodeURIComponent(pathname || "/dashboard")}`);
        }
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to load current user.");
      }

      const payload = (await response.json()) as User;
      setUser(payload);
    } catch (requestError) {
      setUser(null);
      setError(requestError instanceof Error ? requestError.message : "Failed to load current user.");
    } finally {
      setIsLoading(false);
    }
  }

  async function logout() {
    await apiFetch("/api/auth/logout", { method: "POST", body: JSON.stringify({}) });
    setUser(null);
    router.replace("/login");
    router.refresh();
  }

  useEffect(() => {
    void refreshUser();
    // We intentionally refresh when the path changes so protected pages re-check auth.
  }, [pathname]);

  return {
    user,
    isLoading,
    error,
    refreshUser,
    logout,
  };
}
