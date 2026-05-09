import { Button } from "../../../../components/ui/button";
import { Card, CardContent } from "../../../../components/ui/card";
import type { ClarificationCardDto } from "../../../../lib/api/types";

export type TravelIntentPromptSectionProps = {
  data: ClarificationCardDto;
  onSkipPress?: () => void;
};

export const TravelIntentPromptSection = ({
  data,
  onSkipPress,
}: TravelIntentPromptSectionProps): JSX.Element => {
  return (
    <section className="w-full px-[29px]">
      <div className="relative mx-auto w-full max-w-[342px]">
        <Card className="relative overflow-hidden rounded-[15px] border-0 bg-white shadow-[0px_4px_20px_#d0def8] before:pointer-events-none before:absolute before:inset-0 before:z-[1] before:rounded-[15px] before:p-px before:content-[''] before:[background:linear-gradient(180deg,rgba(80,169,254,0.51)_0%,rgba(246,231,90,0.51)_100%)] before:[-webkit-mask:linear-gradient(#fff_0_0)_content-box,linear-gradient(#fff_0_0)] before:[-webkit-mask-composite:xor] before:[mask-composite:exclude]">
          <div className="pointer-events-none absolute left-[115px] top-[34px] h-[242px] w-[293px] rounded-[146.5px/121px] [background:radial-gradient(50%_50%_at_50%_50%,rgba(255,250,215,0.49)_0%,rgba(255,255,255,0.49)_100%)]" />
          <div className="pointer-events-none absolute left-[-109px] top-[-146px] h-[220px] w-[271px] rounded-[135.5px/110px] [background:radial-gradient(50%_50%_at_50%_50%,rgba(209,232,255,0.71)_0%,rgba(255,255,255,0)_100%)]" />
          <CardContent className="relative z-[2] p-0">
            <div className="relative min-h-[226px] px-5 pb-[25px] pt-[19px]">
              <header className="mb-[10px] flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 rounded-xl bg-[linear-gradient(to_bottom_right,rgba(255,209,0,1)_0%,rgba(255,255,255,0)_50%)_bottom_right_/_50%_50%_no-repeat,linear-gradient(to_bottom_left,rgba(255,209,0,1)_0%,rgba(255,255,255,0)_50%)_bottom_left_/_50%_50%_no-repeat,linear-gradient(to_top_left,rgba(255,209,0,1)_0%,rgba(255,255,255,0)_50%)_top_left_/_50%_50%_no-repeat,linear-gradient(to_top_right,rgba(255,209,0,1)_0%,rgba(255,255,255,0)_50%)_top_right_/_50%_50%_no-repeat]" />
                  <h2 className="max-w-[180px] bg-[linear-gradient(42deg,rgba(95,115,128,1)_14%,rgba(62,82,101,1)_75%,rgba(42,114,176,1)_100%)] bg-clip-text text-[15px] font-normal leading-[12.7px] tracking-[0] text-transparent [-webkit-background-clip:text] [-webkit-text-fill-color:transparent] [-webkit-text-stroke:0.49px_transparent] [font-family:'HYQiHei-Regular',Helvetica] [text-fill-color:transparent]">
                    {data.title}
                  </h2>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  className="h-auto rounded-[10.03px] border-[0.84px] border-[#fdffea] bg-[linear-gradient(180deg,rgba(177,212,247,1)_0%,rgba(255,252,230,1)_55%)] px-[17px] py-[6px] text-[10.5px] font-normal leading-[20.3px] tracking-[0] text-[#333c43] shadow-[0px_2px_4px_#00000040] [font-family:'HYQiHei-Regular',Helvetica]"
                  onClick={onSkipPress}
                >
                  {data.skipLabel}
                </Button>
              </header>
              <div className="space-y-[10px]">
                {data.fields.map((field) => (
                  <div key={field.id}>
                    <p className="mb-[7px] whitespace-nowrap text-[10.5px] font-normal leading-[20.3px] tracking-[0] text-[#333c43] [font-family:'HYQiHei-Regular',Helvetica]">
                      {field.question}
                    </p>
                    {field.kind === "chips" && field.options ? (
                      <div className="flex flex-wrap gap-x-[8px] gap-y-[8px]">
                        {field.options.map((option) => (
                          <Button
                            key={option.id}
                            type="button"
                            variant="outline"
                            className="h-auto rounded-[10.03px] border-[0.84px] border-[#d7d7d7] bg-[radial-gradient(50%_50%_at_50%_50%,rgba(225,240,255,0.44)_24%,rgba(255,255,255,0.44)_100%)] px-[17px] py-[3px] text-[10.5px] font-normal leading-[20.3px] tracking-[0] text-[#333c43] shadow-[0px_1px_2px_#d0e7ff] [font-family:'HYQiHei-Regular',Helvetica] hover:bg-[radial-gradient(50%_50%_at_50%_50%,rgba(225,240,255,0.44)_24%,rgba(255,255,255,0.44)_100%)]"
                          >
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    ) : (
                      <Button
                        type="button"
                        variant="outline"
                        className="h-auto rounded-[10.03px] border-[0.84px] border-[#d7d7d7] bg-[radial-gradient(50%_50%_at_50%_50%,rgba(225,240,255,0.44)_24%,rgba(255,255,255,0.44)_100%)] px-[10px] py-[3px] text-[10.5px] font-normal leading-[20.3px] tracking-[0] text-[#333c4347] shadow-[0px_1px_2px_#d0e7ff] [font-family:'HYQiHei-Regular',Helvetica] hover:bg-[radial-gradient(50%_50%_at_50%_50%,rgba(225,240,255,0.44)_24%,rgba(255,255,255,0.44)_100%)]"
                      >
                        {field.placeholder ?? "补充一下..."}
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};
