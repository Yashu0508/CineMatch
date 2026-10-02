"use client";

import { useRef } from "react";
import { Profile } from "@/types";

export const PRESET_AVATARS = [
  { id: "sunset", label: "Sunset", classes: "from-amber-300 to-rose-500", mark: "✦" },
  { id: "ocean", label: "Ocean", classes: "from-cyan-300 to-blue-600", mark: "≈" },
  { id: "forest", label: "Forest", classes: "from-lime-300 to-emerald-700", mark: "◆" },
  { id: "violet", label: "Violet", classes: "from-fuchsia-300 to-violet-700", mark: "●" },
] as const;

function PresetAvatar({ id, size = "size-16" }: { id: string; size?: string }) {
  const preset = PRESET_AVATARS.find(item => item.id === id) ?? PRESET_AVATARS[0];
  return <span aria-hidden="true" className={`grid ${size} shrink-0 place-items-center rounded-full bg-gradient-to-br ${preset.classes} text-2xl font-bold text-black/70 shadow-inner`}>{preset.mark}</span>;
}

export function AvatarVisual({ profile, size = "size-20" }: { profile: Profile; size?: string }) {
  if (profile.avatar_type === "upload" && profile.avatar_url) return <img src={profile.avatar_url} alt="Profile picture" className={`${size} shrink-0 rounded-full object-cover`} />;
  if (profile.avatar_type === "preset" && profile.avatar_id) return <PresetAvatar id={profile.avatar_id} size={size} />;
  return <span className={`${size} grid shrink-0 place-items-center rounded-full bg-amber-300 text-2xl font-semibold text-black`}>{profile.email?.slice(0, 1).toUpperCase() || "C"}</span>;
}

export function AvatarPicker({ profile, busy, onUpload, onPreset, onActivateUpload }: { profile: Profile; busy: boolean; onUpload: (file: File) => void; onPreset: (id: string) => void; onActivateUpload: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const chooseFile = (file?: File) => {
    if (!file) return;
    onUpload(file);
    if (inputRef.current) inputRef.current.value = "";
  };
  return <div className="mt-6 rounded-2xl border border-white/10 bg-white/[.03] p-5">
    <div className="flex flex-wrap items-center gap-4"><AvatarVisual profile={profile} /><div><p className="font-semibold text-white">Profile picture</p><p className="mt-1 text-sm text-white/50">Choose a CineMatch avatar or upload JPEG, PNG, or WebP up to 5 MB.</p></div></div>
    <div className="mt-5 flex flex-wrap gap-3"><input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={event => chooseFile(event.target.files?.[0])} /><button type="button" onClick={() => inputRef.current?.click()} disabled={busy} className="rounded-full bg-amber-300 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50">Upload from computer</button>{profile.has_uploaded_avatar && profile.avatar_type !== "upload" && <button type="button" onClick={onActivateUpload} disabled={busy} className="rounded-full border border-white/15 px-4 py-2 text-sm text-white/75 disabled:opacity-50">Use uploaded image</button>}</div>
    <p className="mt-5 text-xs font-semibold uppercase tracking-[.2em] text-amber-200">CineMatch avatars</p><div className="mt-3 flex flex-wrap gap-3">{PRESET_AVATARS.map(preset => <button key={preset.id} type="button" aria-label={`Choose ${preset.label} avatar`} onClick={() => onPreset(preset.id)} disabled={busy} className={`rounded-full p-1 transition ${profile.avatar_type === "preset" && profile.avatar_id === preset.id ? "bg-amber-300" : "bg-transparent hover:bg-white/20"}`}><PresetAvatar id={preset.id} size="size-14" /></button>)}</div>
  </div>;
}
