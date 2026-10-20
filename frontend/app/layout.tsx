import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FreshLoop | Fresh picks. Less thinking.",
  description: "A smarter way to shop your neighborhood groceries. FreshLoop student project frontend demo.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
