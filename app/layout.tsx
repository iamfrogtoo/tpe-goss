import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import LineBotFab from "@/components/LineBotFab";

export const metadata: Metadata = {
  title: "TPE GOSS | 桃園機場地勤戰情室",
  description: "即時航班與機坪動態資訊平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <body className="antialiased bg-[#0d0d0d] text-white">
        <Navbar />
        {children}
        <Footer />
        <LineBotFab />
      </body>
    </html>
  );
}
