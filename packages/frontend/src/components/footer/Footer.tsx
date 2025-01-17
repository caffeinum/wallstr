import ThemeSwitcher from "@/components/ThemeSwitcher";
import FooterLine from "./FooterLine";

export default function Footer() {
  return (
    <footer className="py-4 text-center text-xs text-base-content/60 bg-base-200">
      <FooterLine />
      <ThemeSwitcher className="abosolute bottom-4 right" />
    </footer>
  );
}
