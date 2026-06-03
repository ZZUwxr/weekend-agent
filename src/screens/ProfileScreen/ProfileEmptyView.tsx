import {
  Bell,
  Car,
  ChevronRight,
  HelpCircle,
  Leaf,
  Settings,
  Sparkles,
  Utensils,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";
import { AppBottomNav } from "../../components/AppBottomNav";
import { AppScreenShell } from "../../components/AppScreenShell";
import { AppToast, useAppToast } from "../../components/AppToast";
import {
  AppActionButton,
  AppBackdrop,
  AppCard,
  AppComposer,
  AppErrorState,
  AppIconButton,
  AppLoadingState,
  AppPageHeader,
  AppPill,
  AppStatusStrip,
} from "../../components/AppUi";
import { EmbeddedStatusBarImage, EmbeddedStatusBarPlaceholder } from "../../components/EmbeddedStatusBar";
import type { ProfilePageDto, ProfilePreferenceRowDto } from "../../lib/api/types";
import {
  tabScreenComposerDockClass,
  tabScreenPrimaryColumnPaddingXClass,
} from "../../lib/tabScreenDockLayout";
import {
  ACTIVITY_PREFERENCES_PATH,
  BUDGET_PACE_PREFERENCES_PATH,
  COMPANION_PROFILES_PATH,
  DIETARY_PREFERENCES_PATH,
  LLM_SETTINGS_PATH,
  TRAVEL_MODE_SETTINGS_PATH,
} from "../../routes";

type Props = { travelId: string; planId: string };

export const PROFILE_GOLD_CARD_CLASS =
  "rounded-[16px] border border-[#e5e7eb] bg-white shadow-[0_8px_24px_rgba(15,23,42,0.06)]";

function preferencePath(kind: ProfilePreferenceRowDto["kind"]): string {
  if (kind === "car") return TRAVEL_MODE_SETTINGS_PATH;
  if (kind === "food") return DIETARY_PREFERENCES_PATH;
  if (kind === "activity") return ACTIVITY_PREFERENCES_PATH;
  return BUDGET_PACE_PREFERENCES_PATH;
}

export function PrefIcon({ row }: { row: ProfilePreferenceRowDto }): JSX.Element {
  const common = "h-4 w-4";
  if (row.kind === "car") return <Car className={`${common} text-[#2456a6]`} strokeWidth={2.1} />;
  if (row.kind === "food") return <Utensils className={`${common} text-[#ea580c]`} strokeWidth={2.1} />;
  if (row.kind === "activity") return <Leaf className={`${common} text-[#0f766e]`} strokeWidth={2.1} />;
  return <Wallet className={`${common} text-[#7c3aed]`} strokeWidth={2.1} />;
}

export type ProfileP2ViewProps = {
  travelId: string;
  planId: string;
  mode: "locked" | "unlocked";
  page: ProfilePageDto | null;
  loadError?: string | null;
};

const lockedRows: ProfilePreferenceRowDto[] = [
  { id: "travel-mode", kind: "car", title: "出行方式与距离", summary: "暂无" },
  { id: "dietary", kind: "food", title: "饮食偏好", summary: "暂无" },
  { id: "activity", kind: "activity", title: "活动偏好", summary: "暂无" },
  { id: "budget", kind: "budget", title: "预算与节奏", summary: "暂无" },
];

function PreferenceRow({
  row,
  flow,
}: {
  row: ProfilePreferenceRowDto;
  flow: { travelId: string; planId: string };
}): JSX.Element {
  return (
    <Link
      to={preferencePath(row.kind)}
      state={flow}
      className="flex min-h-[64px] items-center gap-3 rounded-[14px] bg-[#f8fafc] px-3 py-3 transition active:scale-[0.99]"
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white shadow-[0_4px_12px_rgba(15,23,42,0.05)]">
        <PrefIcon row={row} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-bold leading-5 text-[#111827]">{row.title}</p>
        <p className="mt-0.5 line-clamp-2 text-[12px] leading-5 text-[#64748b]">
          {row.summary?.trim() ? row.summary : "暂无，点击补充"}
        </p>
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-[#94a3b8]" strokeWidth={2.1} />
    </Link>
  );
}

export function ProfileP2View({
  travelId,
  planId,
  mode,
  page,
  loadError,
}: ProfileP2ViewProps): JSX.Element {
  const flow = { travelId, planId };
  const { toastMessage, showToast } = useAppToast();
  const rows = mode === "locked" ? lockedRows : page?.preferenceRows ?? [];
  const defaultStartLine = mode === "locked" ? "默认起点：暂无" : page?.defaultStartLine ?? "默认起点：暂无";
  const archiveTags = mode === "locked" ? [] : page?.archiveTags ?? [];

  return (
    <AppScreenShell frameClassName="bg-[#f8fafc]">
      <AppBackdrop />
      <AppToast message={toastMessage} />
      {page?.statusBarImageUrl ? (
        <EmbeddedStatusBarImage src={page.statusBarImageUrl} className="relative z-20" height={61} width={402} />
      ) : (
        <EmbeddedStatusBarPlaceholder className="relative z-20 bg-white/50" />
      )}

      <div className={`relative z-10 flex min-h-0 flex-1 flex-col pb-2 pt-2 ${tabScreenPrimaryColumnPaddingXClass}`}>
        <AppPageHeader
          eyebrow="我的"
          title={mode === "locked" ? "出行档案" : page?.navTitle ?? "我的"}
          subtitle="你的偏好会影响后续推荐、路线筛选和家庭成员照顾方式。"
          action={
            <AppIconButton label="通知" onClick={() => showToast("暂无新的个人通知")}>
              <Bell className="h-5 w-5" strokeWidth={2.1} />
            </AppIconButton>
          }
        />

        <div className="mt-4 min-h-0 flex-1 overflow-y-auto pb-3">
          {loadError ? (
            <AppErrorState message={loadError} />
          ) : mode === "unlocked" && !page ? (
            <AppLoadingState label="正在加载个人档案..." />
          ) : (
            <div className="space-y-3">
              <AppCard>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div>
                    <h2 className="text-[17px] font-bold leading-6 text-[#111827]">
                      {mode === "locked" ? "同行人出行档案" : page?.archiveSectionTitle ?? "同行人出行档案"}
                    </h2>
                    <p className="mt-0.5 text-[12px] leading-5 text-[#64748b]">同行人和习惯会在推荐里持续生效。</p>
                  </div>
                  <Link
                    to={COMPANION_PROFILES_PATH}
                    state={flow}
                    className="flex min-h-10 shrink-0 items-center justify-center rounded-[12px] bg-[#f1f5f9] px-3 text-[12px] font-bold text-[#334155]"
                  >
                    {archiveTags.length > 0 ? page?.archiveEditLabel ?? "编辑" : "添加"}
                  </Link>
                </div>
                {archiveTags.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {archiveTags.map((tag) => (
                      <AppPill key={tag.id} className="bg-[#fff7df] text-[#92400e]">
                        <span className="mr-1">{tag.iconEmoji}</span>
                        {tag.label}
                      </AppPill>
                    ))}
                  </div>
                ) : (
                  <AppStatusStrip
                    Icon={Sparkles}
                    title="还没有成员档案"
                    detail="添加孩子、伴侣或朋友的偏好后，推荐会更准确。"
                  />
                )}
              </AppCard>

              <AppCard>
                <Link
                  to={LLM_SETTINGS_PATH}
                  state={flow}
                  className="flex min-h-[64px] items-center gap-3 rounded-[14px] bg-[#f8fafc] px-3 py-3 transition active:scale-[0.99]"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-[#2456a6] shadow-[0_4px_12px_rgba(15,23,42,0.05)]">
                    <Settings className="h-4 w-4" strokeWidth={2.1} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[14px] font-bold leading-5 text-[#111827]">设置</p>
                    <p className="mt-0.5 line-clamp-1 text-[12px] leading-5 text-[#64748b]">
                      保存模型、URL 和 API Key
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 shrink-0 text-[#94a3b8]" strokeWidth={2.1} />
                </Link>
              </AppCard>

              <AppCard>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div>
                    <h2 className="text-[17px] font-bold leading-6 text-[#111827]">
                      {page?.memorySectionTitle ?? "记忆与偏好"}
                    </h2>
                    <p className="mt-0.5 text-[12px] leading-5 text-[#64748b]">
                      设置项保存后会回到这里，并在推荐时自动使用。
                    </p>
                  </div>
                  <button
                    type="button"
                    aria-label="说明"
                    onClick={() => showToast("这些偏好会参与路线、餐饮、活动和预算筛选")}
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#f1f5f9] text-[#64748b]"
                  >
                    <HelpCircle className="h-5 w-5" strokeWidth={2.1} />
                  </button>
                </div>
                <div className="space-y-2">
                  {rows.map((row) => (
                    <PreferenceRow key={row.id} row={row} flow={flow} />
                  ))}
                </div>
              </AppCard>
            </div>
          )}
        </div>

        <div className={tabScreenComposerDockClass}>
          <AppActionButton
            tone="blue"
            onClick={() => showToast("可从下方设置项逐个补充偏好")}
          >
            完善出行偏好
          </AppActionButton>
          <AppComposer
            value=""
            onChange={() => undefined}
            onSubmit={() => showToast("从偏好卡片进入具体设置，信息会更完整")}
            placeholder="有疑问可以在这里补充..."
          />
          <AppBottomNav active="我的" journeyFlow={flow} variant="journey" />
        </div>
      </div>
    </AppScreenShell>
  );
}

export function ProfileEmptyView({ travelId, planId }: Props): JSX.Element {
  return <ProfileP2View mode="locked" page={null} travelId={travelId} planId={planId} />;
}
