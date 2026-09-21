import type { Metadata } from "next";
import Admin from "@/components/Admin";
export const metadata: Metadata = {
  title: "Admin",
  robots: { index: false, follow: false },
  alternates: { canonical: "/admin" },
};
export default function Page() {
  return <Admin />;
}
