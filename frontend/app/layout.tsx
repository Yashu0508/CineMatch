import type { Metadata } from "next";
import Providers from "./providers";
import { Nav } from "@/components/navigation/nav";
import "./globals.css";

export const metadata: Metadata = { title: "CineMatch — Find your next favorite", description: "A cinematic movie discovery experience." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><Providers><div className="film-grain" /><Nav /><main>{children}</main></Providers></body></html>;
}
