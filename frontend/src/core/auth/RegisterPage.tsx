import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Eye, EyeOff } from "lucide-react";
import { apiClient } from "@/core/api-client";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Пароли не совпадают");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await apiClient.post("/auth/register", { email, password });
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/");
    } catch (err: unknown) {
      const msg = (err as Error).message ?? "";
      setError(msg.includes("409") ? "Этот email уже зарегистрирован" : "Не удалось создать аккаунт");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen bg-black text-white antialiased font-sans p-2 lg:p-4 selection:bg-white/30">
      <div className="hidden lg:flex relative flex-[0_0_52%] rounded-3xl overflow-hidden">
        <video
          className="absolute inset-0 h-full w-full object-cover"
          src="/assets/hero-background.mp4"
          autoPlay
          muted
          loop
          playsInline
        />
        <div className="absolute inset-0 bg-black/40" />
        <motion.div
          className="relative z-10 flex flex-col justify-end p-12 gap-3"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <motion.p className="text-sm font-medium text-white/60" variants={itemVariants}>
            Трекер
          </motion.p>
          <motion.h1 className="text-4xl font-bold leading-tight" variants={itemVariants}>
            Начнём
          </motion.h1>
          <motion.p className="text-white/60 max-w-xs" variants={itemVariants}>
            Привычки, задачи, финансы и питание — всё в одном месте.
          </motion.p>
        </motion.div>
      </div>

      <motion.div
        className="flex flex-1 flex-col items-center justify-center px-6 lg:px-16"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold mb-8">Регистрация</h2>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-white">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="bg-brand-gray rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 border-none"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-white">Пароль</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  className="w-full bg-brand-gray rounded-xl h-11 px-4 pr-11 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 border-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-white">Подтверждение пароля</label>
              <input
                type={showPassword ? "text" : "password"}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="••••••••"
                required
                className="bg-brand-gray rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 border-none"
              />
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full h-14 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-50"
            >
              {loading ? "Создаём аккаунт…" : "Зарегистрироваться"}
            </button>

            <p className="text-center text-sm text-white/40">
              Уже есть аккаунт?{" "}
              <Link to="/login" className="text-white/70 hover:text-white transition-colors">
                Войти
              </Link>
            </p>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
