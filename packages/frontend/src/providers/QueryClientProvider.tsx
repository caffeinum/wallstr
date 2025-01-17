"use client";
import {QueryClient, QueryClientProvider as TanstackQueryClientProvider} from "@tanstack/react-query";
import {ReactQueryDevtools} from "@tanstack/react-query-devtools";

const queryClient = new QueryClient();

export default function QueryClientProvider({children}: {children: React.ReactNode}) {
  return (
    <TanstackQueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools buttonPosition="bottom-left" />
    </TanstackQueryClientProvider>
  );
}
