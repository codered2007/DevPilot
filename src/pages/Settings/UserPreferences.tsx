import { useEffect, useState } from "react";
import { Bell, Settings2, Save } from "lucide-react";
import {
  getUserPreferences,
  updateUserPreferences,
} from "../../services/api";

interface PreferenceValues {
  theme: "dark" | "light" | "system";
  default_analysis: "review" | "summary" | "architecture";
  response_detail: "concise" | "balanced" | "detailed";
  notifications: boolean;
}

const DEFAULT_PREFERENCES: PreferenceValues = {
  theme: "dark",
  default_analysis: "review",
  response_detail: "balanced",
  notifications: true,
};

function UserPreferences() {
  const [preferences, setPreferences] =
    useState<PreferenceValues>(DEFAULT_PREFERENCES);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const saved = await getUserPreferences();

        setPreferences({
          ...DEFAULT_PREFERENCES,
          ...saved,
        } as PreferenceValues);
      } catch (error) {
        console.error("Failed to load preferences:", error);
        setMessage("Failed to load preferences.");
      } finally {
        setLoading(false);
      }
    };

    loadPreferences();
  }, []);

  const handleChange = <K extends keyof PreferenceValues>(
    key: K,
    value: PreferenceValues[K]
  ) => {
    setPreferences((previous) => ({
      ...previous,
      [key]: value,
    }));

    setMessage("");
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    try {
      await updateUserPreferences(preferences);
      setMessage("Preferences saved successfully.");
    } catch (error) {
      console.error("Failed to save preferences:", error);
      setMessage(
        error instanceof Error
          ? error.message
          : "Failed to save preferences."
      );
    } finally {
      setSaving(false);
    }
  };

  const selectClass =
    "w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm text-zinc-200 outline-none focus:border-blue-500 sm:w-52";

  return (
    <section className="overflow-hidden rounded-xl border border-zinc-800 bg-[#111418]">
      <div className="border-b border-zinc-800 px-4 py-4 sm:px-6 sm:py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
            <Settings2 className="h-4 w-4 text-blue-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-white">
              Preferences
            </h2>

            <p className="mt-0.5 text-xs text-zinc-500">
              Customize your DevPilot experience.
            </p>
          </div>
        </div>
      </div>

      <div className="divide-y divide-zinc-800/70">
        <div className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="text-sm font-medium text-zinc-200">
              Theme
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Choose your preferred appearance.
            </p>
          </div>

          <select
            className={selectClass}
            value={preferences.theme}
            disabled={loading}
            onChange={(event) =>
              handleChange(
                "theme",
                event.target.value as PreferenceValues["theme"]
              )
            }
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </select>
        </div>

        <div className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="text-sm font-medium text-zinc-200">
              Default analysis
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Choose the analysis you use most frequently.
            </p>
          </div>

          <select
            className={selectClass}
            value={preferences.default_analysis}
            disabled={loading}
            onChange={(event) =>
              handleChange(
                "default_analysis",
                event.target.value as PreferenceValues["default_analysis"]
              )
            }
          >
            <option value="review">Repository Review</option>
            <option value="summary">Repository Summary</option>
            <option value="architecture">Architecture Analysis</option>
          </select>
        </div>

        <div className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="text-sm font-medium text-zinc-200">
              AI response detail
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              Set your preferred level of explanation.
            </p>
          </div>

          <select
            className={selectClass}
            value={preferences.response_detail}
            disabled={loading}
            onChange={(event) =>
              handleChange(
                "response_detail",
                event.target.value as PreferenceValues["response_detail"]
              )
            }
          >
            <option value="concise">Concise</option>
            <option value="balanced">Balanced</option>
            <option value="detailed">Detailed</option>
          </select>
        </div>

        <div className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-start gap-3">
            <Bell className="mt-0.5 h-4 w-4 text-zinc-500" />

            <div>
              <p className="text-sm font-medium text-zinc-200">
                Notifications
              </p>
              <p className="mt-1 text-xs text-zinc-500">
                Enable or disable DevPilot notifications.
              </p>
            </div>
          </div>

          <button
            type="button"
            role="switch"
            aria-checked={preferences.notifications}
            disabled={loading}
            onClick={() =>
              handleChange(
                "notifications",
                !preferences.notifications
              )
            }
            className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
              preferences.notifications
                ? "bg-blue-500"
                : "bg-zinc-700"
            }`}
          >
            <span
              className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${
                preferences.notifications
                  ? "translate-x-6"
                  : "translate-x-1"
              }`}
            />
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-3 border-t border-zinc-800 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p
          className={`text-xs ${
            message.includes("successfully")
              ? "text-emerald-400"
              : "text-red-400"
          }`}
        >
          {message}
        </p>

        <button
          type="button"
          onClick={handleSave}
          disabled={loading || saving}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save Preferences"}
        </button>
      </div>
    </section>
  );
}

export default UserPreferences;