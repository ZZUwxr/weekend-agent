import { Baby, ChevronDown as ChevronDownIcon, Search as SearchIcon } from "lucide-react";
import { Card, CardContent } from "../../../../components/ui/card";
import type { NeedsSectionDto } from "../../../../lib/api/types";

export type NeedsStatusAccordionSectionProps = {
  data: NeedsSectionDto;
};

export const NeedsStatusAccordionSection = ({
  data,
}: NeedsStatusAccordionSectionProps): JSX.Element => {
  return (
    <section className="w-full bg-white">
      <Card className="w-full overflow-hidden rounded-[0px_10.98px_10.98px_10.98px] border border-[#fbf3ab] bg-white shadow-[0px_2.75px_13.73px_#00000008]">
        <CardContent className="p-0">
          <header className="flex items-center gap-[5.49px] px-[11px] pt-[11px]">
            <SearchIcon
              className="h-[14px] w-[14px] shrink-0 text-[#1f2937]"
              strokeWidth={1.75}
            />
            <h2 className="flex items-center [font-family:'PingFang_SC-Regular',Helvetica] text-[11px] font-normal leading-[16.5px] tracking-[0] text-[#0f1c2d]">
              {data.headerTitle}
            </h2>
            <div className="flex-1" />
            <ChevronDownIcon
              className="h-[14px] w-[14px] shrink-0 text-[#6b7280]"
              strokeWidth={1.75}
            />
          </header>
          <div className="overflow-x-auto px-[11px] pb-[11px] pt-[7px]">
            <div className="flex min-w-max gap-[5px]">
              {data.cards.map((card, index) => (
                <article
                  key={card.id || `${card.title}-${index}`}
                  className="flex h-[60px] w-[132px] shrink-0 flex-col rounded-[10.03px] border border-[#d7d7d7] bg-[radial-gradient(50%_50%_at_50%_50%,rgba(225,240,255,0.44)_24%,rgba(255,255,255,0.44)_100%)] shadow-[0px_1px_2px_#d0e7ff]"
                >
                  <div className="flex items-center gap-[5.49px] px-[9px] pt-[4px]">
                    {card.icon === "baby" ? (
                      <Baby className="h-[14px] w-[14px] shrink-0 text-[#0f1c2d]" strokeWidth={1.75} />
                    ) : (
                      <span className="flex h-[19.22px] w-[10.68px] items-center justify-center [font-family:'Liberation_Serif-Regular',Helvetica] text-[13.7px] font-normal leading-[19.2px] tracking-[0] text-[#0f1c2d]">
                        {card.icon}
                      </span>
                    )}
                    <span className="[font-family:'WenQuanYi_Zen_Hei-Medium',Helvetica] text-[11px] font-medium leading-[16.5px] tracking-[0] text-[#0f1c2d]">
                      {card.title}
                    </span>
                  </div>
                  <p className="px-[11px] pt-[3.8px] [font-family:'PingFang_SC-Regular',Helvetica] text-[7px] font-normal leading-[11px] tracking-[0] text-[#434655]">
                    {card.description[0]}
                    <br />
                    {card.description[1]}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );
};
