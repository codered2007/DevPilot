interface RepositoryTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  "Overview",
  "Explorer",
  "AI Chat",
  "Docs",
  "Architecture",
];

function RepositoryTabs({
  activeTab,
  onTabChange,
}: RepositoryTabsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900 p-2">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab)}
          className={`rounded-xl px-4 py-2 text-sm transition ${
            activeTab === tab
              ? "bg-blue-600 text-white"
              : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

export default RepositoryTabs;