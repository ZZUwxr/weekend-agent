import type { ReactNode } from "react";
import { useCallback, useLayoutEffect, useRef } from "react";
import { cn } from "../lib/utils";

type Props = {
  children: ReactNode;
  className?: string;
  /** 内容变化时强制重算（如同一路由内异步数据） */
  recalcKey?: string | number;
};

/**
 * 在固定高度容器内按比例缩小内容，尽量一页内展示完全部内容、不出现纵向滚动条（底部导航等应放在此组件之外）。
 * 缩放：z = min(1, avail/need)。若使用「最小缩放下限」会在内容超高时仍可裁切底部，故不设下限。
 * 面向 Capacitor Android WebView；依赖 `zoom`（Chromium）。
 */
export function ContentFitZoom({ children, className, recalcKey }: Props): JSX.Element {
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);

  const fit = useCallback((): void => {
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;

    const avail = outer.clientHeight;
    if (avail <= 0) return;

    const st = inner.style as CSSStyleDeclaration & { zoom?: string };
    st.zoom = "1";
    void inner.offsetHeight;

    const need = inner.scrollHeight;
    const z = need > avail && need > 0 ? Math.min(1, avail / need) : 1;
    st.zoom = String(z);
  }, []);

  useLayoutEffect(() => {
    fit();
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;

    const ro = new ResizeObserver(() => {
      requestAnimationFrame(() => fit());
    });
    ro.observe(outer);
    ro.observe(inner);
    return () => ro.disconnect();
  }, [fit, recalcKey]);

  return (
    <div ref={outerRef} className="min-h-0 flex-1 overflow-hidden">
      {/* className 必须在内层：space-y-* / gap 只对内层「多个子节点」生效；挂在外层时外层仅有一个 inner，间距会整段失效 */}
      <div ref={innerRef} className={cn("w-full min-w-0", className)}>
        {children}
      </div>
    </div>
  );
}
