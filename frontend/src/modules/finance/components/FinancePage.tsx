import { useState } from "react";
import TransactionsTab from "./TransactionsTab";
import AccountsTab from "./AccountsTab";
import SummaryTab from "./SummaryTab";
import RulesTab from "./RulesTab";

type Tab = "transactions" | "accounts" | "summary" | "rules";

const TABS: { value: Tab; label: string }[] = [
  { value: "transactions", label: "Транзакции" },
  { value: "accounts", label: "Счета" },
  { value: "summary", label: "Бюджет" },
  { value: "rules", label: "Правила" },
];

export default function FinancePage() {
  const [tab, setTab] = useState<Tab>("transactions");

  return (
    <div className="max-w-lg mx-auto py-4 px-2 flex flex-col gap-4">
      <h1 className="text-xl font-semibold px-1">Финансы</h1>

      <div className="flex gap-1 px-1 overflow-x-auto">
        {TABS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`px-3 h-8 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
              tab === value
                ? "bg-white/15 text-white"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "transactions" && <TransactionsTab />}
      {tab === "accounts" && <AccountsTab />}
      {tab === "summary" && <SummaryTab />}
      {tab === "rules" && <RulesTab />}
    </div>
  );
}
