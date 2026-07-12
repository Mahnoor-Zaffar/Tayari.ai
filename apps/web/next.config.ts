import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  transpilePackages: ["@tayari/ui", "@tayari/types", "@tayari/config"],
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
}

export default nextConfig
