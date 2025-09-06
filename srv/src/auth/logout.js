import { auth } from "../firebase/config";
import { signOut } from "firebase/auth";

export async function logout() {
  try {
    await signOut(auth);
    console.log("User logged out");
  } catch (error) {
    console.error("Error during logout:", error.code, error.message);
    throw error;
  }
}
