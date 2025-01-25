import ChatInput from "@/components/chat/ChatInput";
import ChatMessages from "@/components/chat/ChatMessages";
import UserMenu from "@/components/user/UserMenu";

export default function AppPage() {
  return (
    <div className="flex flex-col grow">
      <header className="border-b border-base-300 bg-base-100">
        <div className="flex h-16 items-center justify-between px-4">
          <h1 className="text-xl font-semibold">WallStr.chat</h1>
          <UserMenu />
        </div>
      </header>

      <main className="flex-1 overflow-hidden bg-base-200">
        <div className="flex h-full flex-col">
          <ChatMessages />
          <ChatInput />
        </div>
      </main>
    </div>
  );
}
