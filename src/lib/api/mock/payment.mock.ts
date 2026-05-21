import type { PaymentPageDto } from "../types";
import { MOCK_HOME_DASHBOARD } from "./home.mock";

export const MOCK_PAYMENT_PAGE: Omit<PaymentPageDto, "travelId" | "planId"> = {
  statusBarImageUrl: MOCK_HOME_DASHBOARD.statusBarImageUrl,
  voiceInputIconUrl: MOCK_HOME_DASHBOARD.voiceInputIconUrl,
  topProgressText: "正在生成付款…",
  breakdownTitle: "费用明细",
  lineItems: [
    {
      id: "farm",
      itemLabel: "户外亲子农场",
      detailText: "体验项目 1大1小 体验券 (2张)",
      amountText: "¥88.00",
    },
    {
      id: "garden",
      itemLabel: "素然花园",
      detailText: "亲子套票 3人票 (1张)",
      amountText: "¥60.00",
    },
    {
      id: "ride1",
      itemLabel: "第一段叫车",
      detailText: "从酒店到户外亲子农场",
      amountText: "¥15.00",
    },
    {
      id: "ride2",
      itemLabel: "第二段叫车",
      detailText: "从户外亲子农场到素然花园",
      amountText: "到时支付",
    },
    {
      id: "ride3",
      itemLabel: "第三段叫车",
      detailText: "从素然花园回酒店",
      amountText: "到时支付",
    },
  ],
  paymentSectionTitle: "付款方式",
  amountDueBadgeLabel: "本次需支付",
  amountDueValue: "¥163",
  paymentMethods: [
    {
      id: "pm-wechat",
      type: "wechat",
      badgeText: "微",
      label: "微信支付",
      subtitle: "支持储蓄卡、信用卡等",
    },
    {
      id: "pm-alipay",
      type: "alipay",
      badgeText: "支",
      label: "支付宝",
      subtitle: "支持花呗、余额宝等",
    },
    {
      id: "pm-meituan",
      type: "meituan",
      badgeText: "美",
      label: "美团支付",
      subtitle: "快捷支付",
    },
  ],
  defaultSelectedPaymentMethodId: "pm-wechat",
  tapToPayHint: "请点击支付",
  queryBannerText: "支付查询中…",
};
