"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../../hooks/useAuth";
import { login, registerCustomer } from "../../lib/api";
import { createSession, safeNextPath, saveSession } from "../../lib/auth";

type Props = {
  searchParams: Promise<{ next?: string | string[] }>;
};

export default function LoginPage({ searchParams }: Props) {
  const router = useRouter();
  const { session } = useAuth();
  const [nextPath, setNextPath] = useState<string | null>(null);
  const [mode, setMode] = useState<"sign-in" | "register">("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const registering = mode === "register";

  // Search params are read in the effect so the page can still prerender.
  useEffect(() => {
    let cancelled = false;
    void searchParams.then((query) => {
      if (!cancelled) setNextPath(safeNextPath(query.next));
    });
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  // Every successful sign-in lands here, as does an already signed-in visitor.
  useEffect(() => {
    if (session && nextPath !== null) router.replace(nextPath);
  }, [session, nextPath, router]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (registering) {
        await registerCustomer({ email, password, name, phone });
      }
      const token = await login(email, password);
      const nextSession = createSession(token.access_token, token.expires_in);
      if (!nextSession) throw new Error("Sign-in failed. Please try again.");
      saveSession(nextSession);
      // Next keeps this page mounted while hidden; do not retain the password.
      setPassword("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode(registering ? "sign-in" : "register");
    setError("");
  };

  return (
    <main className="journey-page container">
      <Link href="/" className="journey-back">Back to shop</Link>
      <span className="section-kicker">YOUR ACCOUNT</span>
      <h1>{registering ? "Create your account" : "Sign in"}</h1>
      <form className="journey-card auth-form" onSubmit={(event) => void submit(event)}>
        {registering && (
          <>
            <label>
              Full name
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                autoComplete="name"
                required
                maxLength={120}
              />
            </label>
            <label>
              Phone number
              <input
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                autoComplete="tel"
                required
                pattern="\+?[0-9]{9,15}"
                title="9 to 15 digits, optionally starting with +"
              />
            </label>
          </>
        )}
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={registering ? "new-password" : "current-password"}
            required
            minLength={registering ? 8 : 1}
            maxLength={128}
          />
        </label>
        {error && <p className="journey-error" role="alert">{error}</p>}
        <button className="primary-button full" type="submit" disabled={submitting}>
          {submitting
            ? "Please wait..."
            : registering ? "Create account" : "Sign in"}
        </button>
        <button type="button" className="text-button" onClick={switchMode}>
          {registering ? "Already have an account? Sign in" : "New to FreshLoop? Create an account"}
        </button>
      </form>
    </main>
  );
}
