import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@tayari/ui", "@tayari/types", "@tayari/config"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  experimental: {
    serverComponentsExternalPackages: ["@tayari/types"],
  },
};

export default nextConfig;
