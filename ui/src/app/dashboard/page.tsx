"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import { logout } from "@auth/logout";

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <h1>Welcome to the Dashboard!</h1>
      <p>Only logged-in users can see this.</p>
      <button onClick={logout}>Logout</button>
    </ProtectedRoute>
  );
}
