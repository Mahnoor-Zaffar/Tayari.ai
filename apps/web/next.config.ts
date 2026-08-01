import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@tayari/ui", "@tayari/config"],
  serverExternalPackages: ["@tayari/types"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

export default nextConfig;
