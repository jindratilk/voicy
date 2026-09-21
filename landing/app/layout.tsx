import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "./globals.css";
import { site } from "@/lib/site";
export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: "Voicy — Free AI Speech Enhancement for Mac",
    template: "%s · Voicy",
  },
  description:
    "Enhance speech for free, fully on your Mac. Voicy is an open-source AI speech enhancer and local Adobe Podcast alternative. Remove noise without uploading audio.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "Voicy — Your voice. In the clear.",
    description: "Free AI speech enhancement. Fully on your Mac.",
    url: site.url,
    siteName: "Voicy",
    type: "website",
    images: [{ url: "/og.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Voicy — Free AI Speech Enhancement",
    images: ["/og.png"],
  },
  robots: { index: true, follow: true },
  icons: { icon: "/icon.png" },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
