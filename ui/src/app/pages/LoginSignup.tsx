"use client";

import GoogleSignIn from "@/components/googleSignIn";
import Link from "next/link";
import Navbar from "@/components/navbar";
import React, { useState } from "react";
import { Container } from "@/components/container";
import { useRouter } from "next/navigation";
import { signup } from "@/auth/signup";
import { login } from "@/auth/login";

const LoginSignup = () => {
  const [tab, setTab] = useState<"login" | "signup">("login");
  
  // Form state for login
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  
  // Form state for signup
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  
  // Loading states
  const [isLoading, setIsLoading] = useState(false);

  // Router for navigation
  const router = useRouter();

  const googleLogInOnClick = () => {
    // TODO: Integrate Google OAuth login flow
    console.log("Google Login clicked");
  };

  const googleSignUpOnClick = () => {
    // TODO: Integrate Google OAuth signup flow
    console.log("Google Signup clicked");
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const user = await login(loginEmail, loginPassword);
      console.log("Login successful:", user);
      router.push("/dashboard");  // Redirect after login
    } catch (error) {
      if (error instanceof Error) {
        console.error("Signup failed:", error.message);
      } else {
        console.error("Signup failed:", error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const user = await signup(signupEmail, signupPassword);
      console.log("Signup successful:", user);
      router.push("/dashboard");  // Redirect after signup
    } catch (error) {
      if (error instanceof Error) {
        console.error("Signup failed:", error.message);
      } else {
        console.error("Signup failed:", error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center h-screen relative [background:radial-gradient(125%_100%_at_50%_0%,_#FFF_6.32%,_#E0F0FF_29.28%,_#E7EFFD_68.68%,_#FFF_100%)]">
        <div className='max-w-7xl mx-auto absolute inset-0 h-full w-full z-0 pointer-events-none'>
          <div className='absolute inset-y-0 left-0 h-full w-px bg-gradient-to-b from-neutral-400/50 via-neutral-200 to-transparent' />
          <div className='absolute inset-y-0 right-0 h-full w-px bg-gradient-to-b from-neutral-300/50 via-neutral-200 to-transparent' />
        </div>
     <Container>
        <Navbar isLoginPage={true} />

        <main className="flex flex-1 items-center justify-center py-12">
          <div className="w-full max-w-md rounded-2xl bg-white/80 p-10 shadow-lg backdrop-blur-sm border border-gray-200">
            <div className="mb-8">
              <div className="flex border-b border-gray-200">
                <button
                  onClick={() => setTab("login")}
                  className={`flex-1 py-3 px-4 text-center text-sm font-bold border-b-2 focus:outline-none transition-colors duration-300 ${
                    tab === "login"
                      ? "border-sky-500 text-sky-600"
                      : "border-transparent text-gray-500 hover:text-gray-900"
                  }`}
                >
                  Log In
                </button>
                <button
                  onClick={() => setTab("signup")}
                  className={`flex-1 py-3 px-4 text-center text-sm font-bold border-b-2 focus:outline-none transition-colors duration-300 ${
                    tab === "signup"
                      ? "border-sky-500 text-sky-600"
                      : "border-transparent text-gray-500 hover:text-gray-900"
                  }`}
                >
                  Sign Up
                </button>
              </div>
            </div>

            {tab === "login" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-center text-3xl font-extrabold text-gray-900">
                    Welcome Back!
                  </h2>
                  <p className="mt-2 text-center text-sm text-gray-600">
                    Log in to continue your journey.
                  </p>
                </div>
                <form className="space-y-6" onSubmit={handleLoginSubmit}>
                  <div className="space-y-4">
                    <div>
                      <label className="sr-only" htmlFor="login-email">
                        Email address
                      </label>
                      <input
                        id="login-email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        required
                        placeholder="Email address"
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-sky-300 border border-gray-200 bg-white h-14 placeholder:text-gray-500 p-4 text-base font-normal leading-normal"
                      />
                    </div>
                    <div>
                      <label className="sr-only" htmlFor="login-password">
                        Password
                      </label>
                      <input
                        id="login-password"
                        name="password"
                        type="password"
                        autoComplete="current-password"
                        required
                        placeholder="Password"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-sky-300 border border-gray-200 bg-white h-14 placeholder:text-gray-500 p-4 text-base font-normal leading-normal"
                      />
                    </div>
                  </div>
                  <div>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex w-full min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-4 bg-sky-500 text-white text-base font-bold leading-normal tracking-wide shadow-md hover:bg-sky-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-all duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? "Logging in..." : "Log In"}
                    </button>
                  </div>
                </form>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="bg-white/80 px-2 text-gray-600 backdrop-blur-sm">
                      Or log in with
                    </span>
                  </div>
                </div>
                <div>
                    <GoogleSignIn onClick={googleLogInOnClick}/>
                </div>
              </div>
            )}

            {tab === "signup" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-center text-3xl font-extrabold text-gray-900">
                    Create Your Account
                  </h2>
                  <p className="mt-2 text-center text-sm text-gray-600">
                    Join our community of explorers and start planning your next
                    adventure.
                  </p>
                </div>
                <form className="space-y-6" onSubmit={handleSignupSubmit}>
                  <div className="space-y-4">
                    <div>
                      <label className="sr-only" htmlFor="signup-email">
                        Email address
                      </label>
                      <input
                        id="signup-email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        required
                        placeholder="Email address"
                        value={signupEmail}
                        onChange={(e) => setSignupEmail(e.target.value)}
                        className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-sky-300 border border-gray-200 bg-white h-14 placeholder:text-gray-500 p-4 text-base font-normal leading-normal"
                      />
                    </div>
                    <div>
                      <label className="sr-only" htmlFor="signup-password">
                        Password
                      </label>
                      <input
                        id="signup-password"
                        name="password"
                        type="password"
                        autoComplete="new-password"
                        required
                        placeholder="Password"
                        value={signupPassword}
                        onChange={(e) => setSignupPassword(e.target.value)}
                        className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-sky-300 border border-gray-200 bg-white h-14 placeholder:text-gray-500 p-4 text-base font-normal leading-normal"
                      />
                    </div>
                  </div>
                  <div>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="flex w-full min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-12 px-4 bg-sky-500 text-white text-base font-bold leading-normal tracking-wide shadow-md hover:bg-sky-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-all duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? "Creating Account..." : "Create Account"}
                    </button>
                  </div>
                </form>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="bg-white/80 px-2 text-gray-600 backdrop-blur-sm">
                      Or continue with
                    </span>
                  </div>
                </div>
                <div>
                  <GoogleSignIn onClick={googleSignUpOnClick} />
                </div>
                <p className="text-center text-xs text-gray-600">
                  By creating an account, you agree to Tripmate&#39;s
                  <Link className="font-medium text-sky-600 hover:underline" href="/">
                    Terms of Service
                  </Link>{" "}
                  and
                  <Link className="font-medium text-sky-600 hover:underline" href="/">
                    {" "}Privacy Policy
                  </Link>
                  .
                </p>
              </div>
            )}
          </div>
        </main>
     </Container>
    </div>
  );
}

export default LoginSignup;
