/**
 * React Hook for GSAP Animations with Safe Cleanup
 * Source: https://github.com/greensock/GSAP.git
 */

import { useLayoutEffect, useRef, RefObject } from 'react';

// Declaration for optional gsap import
declare const gsap: any;

export function useGsapContext(
  animationCallback: (ctx: any) => void,
  scopeRef?: RefObject<HTMLElement>
) {
  useLayoutEffect(() => {
    if (typeof gsap === 'undefined') return;

    const ctx = gsap.context(() => {
      animationCallback(ctx);
    }, scopeRef?.current || undefined);

    return () => ctx.revert();
  }, [animationCallback, scopeRef]);
}
