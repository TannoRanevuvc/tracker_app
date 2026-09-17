import { Trophy, Lock } from "lucide-react";
import { motion } from "motion/react";
import { useMotivationSummary, useMotivationAchievements } from "../hooks";
import type { Achievement } from "../types";

const listVariants = {
  visible: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.1 } },
  hidden: { opacity: 0 },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

function XpBar({ xpTotal, xpToNext }: { xpTotal: number; xpToNext: number }) {
  const progress = xpTotal % 100;
  const pct = Math.round((progress / 100) * 100);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs text-white/40">
        <span>{progress} / 100 XP</span>
        <span>ещё {xpToNext} XP</span>
      </div>
      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-white transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function AchievementCard({ achievement }: { achievement: Achievement }) {
  const unlocked = achievement.unlocked;
  return (
    <div
      className={`bg-brand-gray rounded-3xl p-5 flex items-start gap-4 ${
        unlocked ? "" : "opacity-40"
      }`}
    >
      <div className="mt-0.5 shrink-0">
        {unlocked ? (
          <Trophy size={20} className="text-white" />
        ) : (
          <Lock size={20} className="text-white/60" />
        )}
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-sm font-semibold leading-tight">{achievement.name}</span>
        <span className="text-xs text-white/40 leading-snug">{achievement.description}</span>
        {unlocked && achievement.unlocked_at && (
          <span className="text-xs text-white/20 mt-1">
            {new Date(achievement.unlocked_at).toLocaleDateString("ru-RU")}
          </span>
        )}
      </div>
    </div>
  );
}

function sortAchievements(achievements: Achievement[]): Achievement[] {
  const unlocked = achievements
    .filter((a) => a.unlocked)
    .sort((a, b) => {
      if (!a.unlocked_at || !b.unlocked_at) return 0;
      return new Date(b.unlocked_at).getTime() - new Date(a.unlocked_at).getTime();
    });
  const locked = achievements
    .filter((a) => !a.unlocked)
    .sort((a, b) => a.name.localeCompare(b.name, "ru"));
  return [...unlocked, ...locked];
}

export default function MotivationPage() {
  const { data: summary, isLoading: summaryLoading, isError: summaryError } = useMotivationSummary();
  const { data: achievements = [], isLoading: achLoading } = useMotivationAchievements();

  const isLoading = summaryLoading || achLoading;
  const sorted = sortAchievements(achievements);

  return (
    <div className="max-w-lg mx-auto py-4 px-2 flex flex-col gap-4">
      <div className="flex items-center justify-between px-1">
        <h1 className="text-xl font-semibold">Мотивация</h1>
      </div>

      {isLoading && (
        <div className="flex justify-center pt-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {summaryError && (
        <p className="text-center text-white/40 pt-12 text-sm">
          Не удалось загрузить данные
        </p>
      )}

      {!isLoading && summary && (
        <motion.div
          className="flex flex-col gap-3"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Level card */}
          <motion.div variants={itemVariants} className="bg-brand-gray rounded-3xl p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs text-white/40 uppercase tracking-widest">Уровень</span>
                <span className="text-4xl font-bold leading-none">{summary.level}</span>
              </div>
              <div className="flex flex-col items-end gap-0.5">
                <span className="text-xs text-white/40">Всего XP</span>
                <span className="text-2xl font-semibold">{summary.xp_total}</span>
              </div>
            </div>
            <XpBar xpTotal={summary.xp_total} xpToNext={summary.xp_to_next_level} />
          </motion.div>

          {/* Recent achievements */}
          {summary.recent_achievements.length > 0 && (
            <motion.div variants={itemVariants} className="bg-brand-gray rounded-3xl p-5 flex flex-col gap-3">
              <span className="text-xs text-white/40 uppercase tracking-widest">Последние достижения</span>
              <div className="flex flex-col gap-2">
                {summary.recent_achievements.map((a) => (
                  <div key={a.code} className="flex items-center gap-3">
                    <Trophy size={14} className="text-white/60 shrink-0" />
                    <span className="text-sm">{a.name}</span>
                    <span className="ml-auto text-xs text-white/20">
                      {new Date(a.unlocked_at).toLocaleDateString("ru-RU")}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* All achievements */}
          {sorted.length > 0 && (
            <>
              <div className="px-1 pt-1">
                <span className="text-xs text-white/40 uppercase tracking-widest">Достижения</span>
              </div>
              {sorted.map((a) => (
                <motion.div key={a.code} variants={itemVariants}>
                  <AchievementCard achievement={a} />
                </motion.div>
              ))}
            </>
          )}
        </motion.div>
      )}
    </div>
  );
}
