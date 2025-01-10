import type { Meta, StoryObj } from "@storybook/react";
import { within, userEvent } from "@storybook/test";

import SignInForm from "../SignInForm";

const meta: Meta<typeof SignInForm> = {
  title: "components/auth/SignInForm",
  component: SignInForm,
  args: {
    urls: {
      forgotPassword: "#",
      signUp: "#",
    },
  },
};

export default meta;

type TStory = StoryObj<typeof meta>;

export const Default: TStory = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    await userEvent.type(canvas.getByLabelText("Email"), "email@example.com");
    await userEvent.type(canvas.getByLabelText("Password"), "password123");

    await userEvent.click(canvas.getByRole("button"));
  },
};
