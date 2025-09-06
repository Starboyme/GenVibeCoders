import { auth } from "./firebase/config.js";
import { signInWithEmailAndPassword } from "firebase/auth";

export async function login(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    console.log("User logged in:", userCredential.user);
    return userCredential.user;
  } catch (error) {
    console.error("Error during login: ", error.code, error.message);
    throw error;
  }
}
