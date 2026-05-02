import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root so Turbopack doesn't get confused by the
  // backend lockfile sitting one directory up.
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
