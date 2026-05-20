import { Button } from "../../../../components/ui/button";
import type { ClarificationCardDto } from "../../../../lib/api/types";
import { FIGMA_CHAT_177 } from "../../../../lib/api/mock/figma-chat-177-assets";

export type TravelIntentPromptSectionProps = {
  data: ClarificationCardDto;
  onSkipPress?: () => void;
};

/** Figma node 1:117 · 「想确认一下」卡片渐变标题 */
function clarifyTitleGradientClass(): string {
  return "bg-[linear-gradient(28.101145957433033deg,rgb(95,115,128)_16.391%,rgb(62,82,101)_73.16%,rgb(42,114,176)_96.32%)] bg-clip-text text-transparent [-webkit-background-clip:text]";
}

export const TravelIntentPromptSection = ({
  data,
  onSkipPress,
}: TravelIntentPromptSectionProps): JSX.Element => {
  return (
    <section className="w-full">
      <div className="relative mx-auto min-h-[226px] w-[342px] shrink-0 overflow-hidden rounded-[15px] border border-[#50a9fe] bg-white shadow-[0px_4px_20px_0px_#d0def8]">
        <img
          src={FIGMA_CHAT_177.cardGlowYellow}
          alt=""
          className="pointer-events-none absolute left-[114px] top-[33px] h-[242px] w-[293px] max-w-none object-cover opacity-95"
        />
        <img
          src={FIGMA_CHAT_177.cardGlowBlue}
          alt=""
          className="pointer-events-none absolute -left-[110px] -top-[147px] h-[220px] w-[271px] max-w-none object-cover opacity-90"
        />
        <div className="relative z-[2] px-[19px] pb-[21px] pt-[18px]">
          <header className="relative mb-[9px] flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <img
                src={FIGMA_CHAT_177.clarificationHeaderOrb}
                alt=""
                width={24}
                height={24}
                className="h-6 w-6 shrink-0 object-contain"
              />
              <h2
                className={`min-w-0 pt-0.5 [font-family:'HYQiHei-Regular',Helvetica] text-[15px] font-normal leading-[12.654px] ${clarifyTitleGradientClass()}`}
              >
                {data.title}
              </h2>
            </div>
            <Button
              type="button"
              variant="ghost"
              className="h-auto shrink-0 rounded-[10.027px] border-[0.836px] border-[#fdffea] bg-gradient-to-b from-[#b1d4f7] to-[#fffce6] to-[54.808%] px-[17px] py-[6px] [font-family:'HYQiHei-Regular',Helvetica] text-[10.505px] font-normal leading-[20px] tracking-[0] text-[#343d43] shadow-[0px_2px_4px_rgba(0,0,0,0.25)]"
              onClick={onSkipPress}
            >
              {data.skipLabel}
            </Button>
          </header>
          <div className="space-y-[17px]">
            {data.fields.map((field) => (
              <div key={field.id}>
                <p className="mb-[9px] [font-family:'HYQiHei-Regular',Helvetica] text-[10.505px] font-normal leading-[20.322px] text-[#343d43]">
                  {field.question}
                </p>
                {field.kind === "chips" && field.options ? (
                  <div className="flex flex-wrap gap-x-2 gap-y-2">
                    {field.options.map((option) => {
                      const selected = field.selectedOptionIds?.includes(option.id) ?? false;
                      const borderCls = selected ? "border-[#ffd100]" : "border-[#d8d8d8]";
                      return (
                        <Button
                          key={option.id}
                          type="button"
                          variant="outline"
                          className={`h-auto min-h-[26px] rounded-[10.027px] border-[0.836px] bg-[linear-gradient(rgba(225,240,255,0.44)_23.58%,rgba(255,255,255,0.44)_100%)] px-[10px] py-[6px] [font-family:'HYQiHei-Regular',Helvetica] text-[10.505px] font-normal leading-[20.322px] text-[#343d43] shadow-[0px_1px_2px_0px_#d1e8ff] ${borderCls} hover:bg-[linear-gradient(rgba(225,240,255,0.44)_23.58%,rgba(255,255,255,0.44)_100%)]`}
                        >
                          {option.label}
                        </Button>
                      );
                    })}
                  </div>
                ) : (
                  <Button
                    type="button"
                    variant="outline"
                    className="h-auto min-h-[26px] rounded-[10.027px] border-[0.836px] border-[#d8d8d8] bg-[linear-gradient(rgba(225,240,255,0.44)_23.58%,rgba(255,255,255,0.44)_100%)] px-[10px] py-[6px] [font-family:'HYQiHei-Regular',Helvetica] text-[10.505px] font-normal leading-[20.322px] text-[#343d43]/[0.28] shadow-[0px_1px_2px_0px_#d1e8ff] hover:bg-[linear-gradient(rgba(225,240,255,0.44)_23.58%,rgba(255,255,255,0.44)_100%)]"
                  >
                    {field.placeholder ?? "补充一下..."}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
