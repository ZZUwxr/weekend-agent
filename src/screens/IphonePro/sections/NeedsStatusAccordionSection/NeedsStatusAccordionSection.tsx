import { Baby } from "lucide-react";
import { FIGMA_CHAT_177 } from "../../../../lib/api/mock/figma-chat-177-assets";
import type { NeedsSectionDto } from "../../../../lib/api/types";

export type NeedsStatusAccordionSectionProps = {
  data: NeedsSectionDto;
};

export const NeedsStatusAccordionSection = ({
  data,
}: NeedsStatusAccordionSectionProps): JSX.Element => {
  return (
    <section className="w-full">
      <div className="w-full rounded-bl-[10.983px] rounded-br-[10.983px] rounded-tr-[10.983px] border-[0.5px] border-[#fbf3ab] bg-white shadow-[0px_2.746px_6.864px_rgba(0,0,0,0.03)]">
        <header className="flex items-center gap-[5.5px] px-[10.5px] pb-0 pt-[10.5px]">
          <img
            src={FIGMA_CHAT_177.needsSearchIcon}
            alt=""
            className="h-[10px] w-[10px] shrink-0 object-contain"
          />
          <div className="min-w-0 flex-1 leading-[16.475px] [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] text-[10.983px] font-normal text-[#0f1c2d]">
            {data.headerTitle}
          </div>
          <img
            src={FIGMA_CHAT_177.needsHeaderChevron}
            alt=""
            className="h-[5.5px] w-[8px] shrink-0 object-contain opacity-70"
          />
        </header>
        <div className="overflow-x-auto px-[10.5px] pb-[10.5px] pt-[9px]">
          <div className="flex w-max gap-[5px]">
            {data.cards.map((card, index) => {
              // 拼成连续正文交由浏览器换行，避免两句话被拆进数组两段时在中间硬拆汉字
              const bodyText = card.description
                .map((s) => s.trim())
                .filter(Boolean)
                .join("");
              return (
              <article
                key={card.id || `${card.title}-${index}`}
                className="flex min-h-[59px] w-[132px] shrink-0 flex-col rounded-[10.027px] border-[0.836px] border-[#d8d8d8] bg-[linear-gradient(rgba(225,240,255,0.44)_23.6%,rgba(255,255,255,0.44)_100%)] shadow-[0px_1px_2px_0px_#d1e8ff]"
              >
                <div className="flex items-center gap-[5.5px] px-2 pb-0 pt-[3px]">
                  {card.icon === "baby" ? (
                    <Baby className="h-[13px] w-[13px] shrink-0 text-[#0f1c2d]" strokeWidth={1.75} />
                  ) : (
                    <span className="flex min-h-[19px] min-w-[11px] items-center justify-center [font-family:'Liberation_Serif','PingFang_SC',sans-serif] text-[13.7px] font-normal leading-[19px] text-[#0f1c2d]">
                      {card.icon}
                    </span>
                  )}
                  <span className="[font-family:'WenQuanYi_Zen_Hei','Zen_Hei','PingFang_SC',sans-serif] text-[11px] font-medium leading-[16.5px] text-[#0f1c2d]">
                    {card.title}
                  </span>
                </div>
                <div
                  className={
                    "min-h-0 flex-1 px-[10px] pb-[7px] pt-[6px] [font-family:'PingFang_SC','PingFang_SC-Regular',sans-serif] " +
                    "text-[7px] font-normal leading-[1.65] text-[#434655] [word-break:keep-all] [overflow-wrap:anywhere]"
                  }
                >
                  {bodyText ? (
                    <p className="m-0 hyphens-none [-webkit-text-size-adjust:100%] [text-size-adjust:100%]">
                      {bodyText}
                    </p>
                  ) : null}
                </div>
              </article>
            );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};
