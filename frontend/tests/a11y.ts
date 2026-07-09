import { axe } from 'vitest-axe'

// jsdom performs no layout or paint, so axe's `color-contrast` rule can only
// return "incomplete" (getComputedStyle yields no real colors). Disable it here
// and keep contrast as a separate computed gate (see the P4.5 audit). This axe
// pass still covers roles, accessible names, label association, landmarks,
// heading order, list/table markup, aria-* validity and duplicate ids.
export function axeCheck(container: Element) {
  return axe(container, { rules: { 'color-contrast': { enabled: false } } })
}
