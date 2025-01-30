import {ThemeProvider} from "next-themes";

import Footer from "@/components/footer/Footer";
import Header from "@/components/header/Header";

export default function AppLayout({children}: {children: React.ReactNode}) {
  return (
    <ThemeProvider>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="grow flex">{children}</main>
        <Footer />
      </div>
    </ThemeProvider>
  );
}
