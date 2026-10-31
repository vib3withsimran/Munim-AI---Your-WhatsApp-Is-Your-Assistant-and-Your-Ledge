import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Munim AI — Aapke Dukaan Ka Digital Munim",
  description:
    "WhatsApp par hi orders lo, payments track karo, customer ki baatein yaad rakho — sab automatic, simple aur aapki apni bhasha mein.",
  keywords: ["munim ai", "whatsapp business", "small business india", "order management", "hinglish"],
  openGraph: {
    title: "Munim AI",
    description: "WhatsApp se chhote business ka poora hisaab-kitab",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0d1410",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hi">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
