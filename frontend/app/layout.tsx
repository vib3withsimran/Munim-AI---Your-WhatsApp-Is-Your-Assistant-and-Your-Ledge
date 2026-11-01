import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
<<<<<<< Updated upstream

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});
=======
>>>>>>> Stashed changes

export const metadata: Metadata = {
  title: "Munim AI — Aapke Dukaan Ka Digital Munim",
  description:
    "WhatsApp par hi orders lo, payments track karo, customer ki baatein yaad rakho — sab automatic, simple aur aapki apni bhasha mein.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#07110D",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
<<<<<<< Updated upstream
    <html lang="hi" className={plusJakartaSans.variable}>
      <body className="antialiased bg-[#07110D] text-[#F0FDF4] min-h-screen">
=======
    <html lang="hi">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
>>>>>>> Stashed changes
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
