import type { Preview } from "@storybook/react";

import { MINIMAL_VIEWPORTS } from "@storybook/addon-viewport";

import { withAppRouterContext } from "./AppRouterContextMock";
import "../app/globals.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    viewport: {
      viewports: MINIMAL_VIEWPORTS,
    },
    layout: "centered",
    nextjs: {
      appDirectory: true,
    },
  },
  decorators: [withAppRouterContext],
};

export default preview;
