import { navItems } from "./nav";

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <nav className="border-b px-4 py-3">
        {navItems.map((item) => (
          <a key={item.path} href={item.path} className="mr-4">
            {item.label}
          </a>
        ))}
      </nav>
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
}
