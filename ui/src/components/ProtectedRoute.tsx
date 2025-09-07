"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/auth/trackAuthState";
import { User } from "firebase/auth"; // TS type for user

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = getCurrentUser((user: User | null) => {
      if (!user) {
        router.push("/login"); // Redirect if not logged in
      }
      setLoading(false);
    });

    return () => unsubscribe(); // cleanup listener
  }, [router]);

  if (loading) {
    return <p>Loading...</p>; // or a spinner
  }

  return <>{children}</>;
}
