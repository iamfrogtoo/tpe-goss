import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        // 靜態 bundle（JS/CSS）永久快取，hash 保證唯一不衝突
        source: "/_next/static/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
      {
        // 所有頁面 HTML 不快取，強制 Cloudflare 和瀏覽器每次取新版
        // 這樣每次 npm build 後修改立即生效，不會拿到舊版 JS
        source: "/((?!_next/static|_next/image|favicon.ico).*)",
        headers: [
          { key: "Cache-Control", value: "no-store, must-revalidate" },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      // 移除指向私有 IP 的重寫規則，避免 Vercel 部署時連接超時
      // {
      //   source: '/api/data/:path*',
      //   destination: 'http://192.168.31.19:8080/dashboard/data/:path*',
      // },
    ];
  },
};

export default nextConfig;
