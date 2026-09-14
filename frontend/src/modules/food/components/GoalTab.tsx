import { useState } from "react";
import { useCurrentGoal, useCreateGoal } from "../hooks";

export default function GoalTab() {
  const today = new Date().toISOString().slice(0, 10);
  const { data: goal, isLoading } = useCurrentGoal();
  const createGoal = useCreateGoal();

  const [kcal, setKcal] = useState("");
  const [protein, setProtein] = useState("");
  const [fat, setFat] = useState("");
  const [carbs, setCarbs] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState(today);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createGoal.mutate(
      {
        kcal_goal: parseInt(kcal, 10),
        ...(protein && { protein_goal_g: parseInt(protein, 10) }),
        ...(fat && { fat_goal_g: parseInt(fat, 10) }),
        ...(carbs && { carbs_goal_g: parseInt(carbs, 10) }),
        effective_from: effectiveFrom,
      },
      {
        onSuccess: () => {
          setKcal("");
          setProtein("");
          setFat("");
          setCarbs("");
          setEffectiveFrom(today);
        },
      }
    );
  }

  const validKcal = /^\d+$/.test(kcal.trim()) && parseInt(kcal, 10) > 0;

  return (
    <div className="flex flex-col gap-4">
      {isLoading ? (
        <div className="flex justify-center pt-8">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      ) : goal ? (
        <div className="bg-brand-gray rounded-3xl px-5 py-4 flex flex-col gap-3">
          <p className="text-sm text-white/40">Текущая цель</p>
          <div className="flex items-end gap-1">
            <span className="text-3xl font-semibold">{goal.kcal_goal}</span>
            <span className="text-white/40 text-sm mb-1">ккал/день</span>
          </div>
          <div className="flex gap-4 text-sm">
            {goal.protein_goal_g != null && (
              <span className="text-white/60">Б: {goal.protein_goal_g} г</span>
            )}
            {goal.fat_goal_g != null && (
              <span className="text-white/60">Ж: {goal.fat_goal_g} г</span>
            )}
            {goal.carbs_goal_g != null && (
              <span className="text-white/60">У: {goal.carbs_goal_g} г</span>
            )}
          </div>
          <p className="text-xs text-white/30">с {goal.effective_from}</p>
        </div>
      ) : (
        <p className="text-white/40 text-sm text-center pt-4">Цель ещё не задана</p>
      )}

      <div className="bg-brand-gray rounded-3xl px-5 py-5 flex flex-col gap-4">
        <p className="text-sm font-medium">{goal ? "Изменить цель" : "Задать цель"}</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-white">Калории, ккал</label>
            <input
              type="text"
              inputMode="numeric"
              value={kcal}
              onChange={(e) => setKcal(e.target.value)}
              placeholder="2000"
              required
              className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
            />
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium text-white/60">Белки, г</label>
              <input
                type="text"
                inputMode="numeric"
                value={protein}
                onChange={(e) => setProtein(e.target.value)}
                placeholder="—"
                className="bg-black/40 rounded-xl h-11 px-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 text-sm"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium text-white/60">Жиры, г</label>
              <input
                type="text"
                inputMode="numeric"
                value={fat}
                onChange={(e) => setFat(e.target.value)}
                placeholder="—"
                className="bg-black/40 rounded-xl h-11 px-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 text-sm"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium text-white/60">Углев., г</label>
              <input
                type="text"
                inputMode="numeric"
                value={carbs}
                onChange={(e) => setCarbs(e.target.value)}
                placeholder="—"
                className="bg-black/40 rounded-xl h-11 px-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 text-sm"
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-white">Действует с</label>
            <input
              type="date"
              value={effectiveFrom}
              onChange={(e) => setEffectiveFrom(e.target.value)}
              required
              className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
            />
          </div>

          {createGoal.isError && (
            <p className="text-red-400 text-sm">Не удалось сохранить цель</p>
          )}

          <button
            type="submit"
            disabled={createGoal.isPending || !validKcal}
            className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40 mt-1"
          >
            {createGoal.isPending ? "Сохраняем…" : "Сохранить"}
          </button>
        </form>
      </div>
    </div>
  );
}
