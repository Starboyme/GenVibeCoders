import { auth } from "../firebase/config";
import { createUserWithEmailAndPassword } from "firebase/auth";

export async function signup(email, password) {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    console.log("User signed up:", userCredential.user);
    return userCredential.user;
  } catch (error) {
    console.error("Error during signup", error.code, error.message);
    throw error;
  }
}
