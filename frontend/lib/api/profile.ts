import { Profile } from "@/types";
import { apiFetch } from "./client";

export const profileApi = {
  get: () => apiFetch<Profile>("/users/profile"),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return apiFetch<Profile>("/users/avatar/upload", { method: "POST", body });
  },
  selectPreset: (avatarId: string) => apiFetch<Profile>("/users/avatar/preset", { method: "PUT", body: JSON.stringify({ avatar_id: avatarId }) }),
  activateUpload: () => apiFetch<Profile>("/users/avatar/upload/activate", { method: "PUT" }),
};
