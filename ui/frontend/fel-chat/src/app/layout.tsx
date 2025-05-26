import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "FEE.lix Chat",
  description: "Ask FEE.lix anything about your studies",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}