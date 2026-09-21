/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.overrideBundlerConfig((current) => {
  const withTailwind = enableTailwind(current);
  return {
    ...withTailwind,
    watchOptions: {
      ...withTailwind.watchOptions,
      poll: 1000,
      aggregateTimeout: 300,
      ignored: ["**/node_modules/**"],
    },
  };
});
