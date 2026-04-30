import { Loader2, Radio, Send } from "lucide-react";

import { Button } from "../common/button";
import { Card, CardBody, CardHeader } from "../common/card";
import { FieldLabel, TextArea, TextInput } from "../common/field";
import type { PlanPreviewRequest } from "../../types/plan";

interface PlanFormProps {
  value: PlanPreviewRequest;
  isPreviewing: boolean;
  isStreaming: boolean;
  onChange: (next: PlanPreviewRequest) => void;
  onPreview: () => void;
  onStream: () => void;
}

export function PlanForm({
  value,
  isPreviewing,
  isStreaming,
  onChange,
  onPreview,
  onStream,
}: PlanFormProps) {
  const disabled = isPreviewing || isStreaming;

  return (
    <Card>
      <CardHeader>
        <h2 className="text-base font-semibold">规划输入</h2>
      </CardHeader>
      <CardBody className="space-y-4">
        <div className="space-y-2">
          <FieldLabel htmlFor="query">自然语言需求</FieldLabel>
          <TextArea
            id="query"
            value={value.query}
            onChange={(event) => onChange({ ...value, query: event.target.value })}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <FieldLabel htmlFor="user-id">用户</FieldLabel>
            <TextInput
              id="user-id"
              value={value.user_id}
              onChange={(event) => onChange({ ...value, user_id: event.target.value })}
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="city">城市</FieldLabel>
            <TextInput
              id="city"
              value={value.city}
              onChange={(event) => onChange({ ...value, city: event.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-[1fr_120px] gap-3">
          <div className="space-y-2">
            <FieldLabel htmlFor="start-time">开始时间</FieldLabel>
            <TextInput
              id="start-time"
              type="datetime-local"
              value={value.start_time.slice(0, 16)}
              onChange={(event) =>
                onChange({ ...value, start_time: `${event.target.value}:00` })
              }
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="duration">分钟</FieldLabel>
            <TextInput
              id="duration"
              type="number"
              min={30}
              max={720}
              value={value.duration_minutes}
              onChange={(event) =>
                onChange({ ...value, duration_minutes: Number(event.target.value) })
              }
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <FieldLabel htmlFor="lat">纬度</FieldLabel>
            <TextInput
              id="lat"
              type="number"
              step="0.0001"
              value={value.location?.lat ?? ""}
              onChange={(event) =>
                onChange({
                  ...value,
                  location: {
                    lat: Number(event.target.value),
                    lon: value.location?.lon ?? 114.05,
                  },
                })
              }
            />
          </div>
          <div className="space-y-2">
            <FieldLabel htmlFor="lon">经度</FieldLabel>
            <TextInput
              id="lon"
              type="number"
              step="0.0001"
              value={value.location?.lon ?? ""}
              onChange={(event) =>
                onChange({
                  ...value,
                  location: {
                    lat: value.location?.lat ?? 22.54,
                    lon: Number(event.target.value),
                  },
                })
              }
            />
          </div>
        </div>

        <div className="flex gap-3 pt-1">
          <Button className="flex-1" disabled={disabled} onClick={onPreview}>
            {isPreviewing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            直接生成
          </Button>
          <Button
            className="flex-1"
            disabled={disabled}
            variant="secondary"
            onClick={onStream}
          >
            {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Radio className="h-4 w-4" />}
            流式规划
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
