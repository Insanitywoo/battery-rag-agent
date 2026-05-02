"use client";

type LogoutButtonProps = {
  onLogout: () => Promise<void>;
  className?: string;
};

export function LogoutButton({ onLogout, className }: LogoutButtonProps) {
  return (
    <button
      type="button"
      onClick={() => void onLogout()}
      className={
        className ??
        "rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
      }
    >
      Logout
    </button>
  );
}
