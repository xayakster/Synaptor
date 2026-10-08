/**
 * GSAP Helper Utilities for Web Applications
 * Source: https://github.com/greensock/GSAP.git
 */

export function createScrollTriggerAnimation(gsapInstance, options) {
  const {
    trigger,
    target = trigger,
    animation = { y: 30, opacity: 0, duration: 0.6, ease: "power2.out" },
    start = "top 80%",
    toggleActions = "play none none reverse"
  } = options;

  return gsapInstance.from(target, {
    ...animation,
    scrollTrigger: {
      trigger,
      start,
      toggleActions
    }
  });
}

export function createStaggeredReveal(gsapInstance, container, itemsSelector = ".stagger-item") {
  return gsapInstance.from(`${container} ${itemsSelector}`, {
    y: 35,
    opacity: 0,
    duration: 0.7,
    stagger: 0.1,
    ease: "power3.out"
  });
}
