import type { Metadata } from "next";
import { VT323 } from "next/font/google";
import "./globals.css";
import { CRTOverlay } from "@/components/effects/CRTOverlay";

const vt323 = VT323({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-vt323',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "FALSE FLAG | Situation Room",
  description: "Crisis Simulation Terminal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`theme-defcon ${vt323.variable}`}>
      <body className="bg-black text-white antialiased relative overflow-hidden h-screen w-screen font-vt323 text-lg">
        <CRTOverlay />
        <div className="relative z-10 h-full w-full">
            {children}
        </div>
      </body>
    </html>
  );
}
