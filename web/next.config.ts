import type { NextConfig } from "next";

const api = process.env.API_INTERNAL_URL || "http://127.0.0.1:43124";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  agentRules: false,
  async rewrites() {
    const catalog = ["meta", "session", "profiles", "careers", "courses", "programs", "transcripts"];
    return [
      ...catalog.flatMap((route) => [
        { source: `/api/${route}`, destination: `${api}/api/${route}` },
        { source: `/api/${route}/:path*`, destination: `${api}/api/${route}/:path*` },
      ]),
      { source: "/health", destination: `${api}/health` },
    ];
  },
};

export default nextConfig;
