import { useState } from "react";
import DiaryTab from "./DiaryTab";
import ProductsTab from "./ProductsTab";
import GoalTab from "./GoalTab";

type Tab = "diary" | "products" | "goal";

const TABS: { value: Tab; label: string }[] = [
  { value: "diary", label: "Дневник" },
  { value: "products", label: "Продукты" },
  { value: "goal", label: "Цель" },
];

export default function FoodPage() {
  const [tab, setTab] = useState<Tab>("diary");

  return (
    <div className="max-w-lg mx-auto py-4 px-2 flex flex-col gap-4">
      <h1 className="text-xl font-semibold px-1">Питание</h1>

      <div className="flex gap-1 px-1">
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

      {tab === "diary" && <DiaryTab />}
      {tab === "products" && <ProductsTab />}
      {tab === "goal" && <GoalTab />}
    </div>
  );
}
