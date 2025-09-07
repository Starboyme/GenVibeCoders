import { auth } from "../firebase/config";
import { onAuthStateChanged } from "firebase/auth";

export function getCurrentUser(callback) {
  return onAuthStateChanged(auth, (user) => {
    callback(user);
  });
}
