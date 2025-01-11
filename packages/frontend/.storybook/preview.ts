import type { Preview } from "@storybook/react";

import { MINIMAL_VIEWPORTS } from "@storybook/addon-viewport";

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
  },
};

export default preview;
