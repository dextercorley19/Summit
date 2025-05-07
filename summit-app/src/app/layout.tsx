import type { Metadata } from "next";
import { inter } from "./fonts";
import "./globals.css";
import { ClerkProvider } from "@clerk/nextjs";

export const metadata: Metadata = {
  title: "Summit",
  description: "Your GitHub dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${inter} antialiased`}>{children}</body>
      </html>
    </ClerkProvider>
  );
}
