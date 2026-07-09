// vitest-axe ships its matcher type augmentation against the legacy `Vi.Assertion`
// global namespace, which Vitest 2.x no longer reads. Re-declare it against the
// `vitest` module's `Assertion` interface (the same pattern @testing-library/jest-dom
// uses) so `expect(results).toHaveNoViolations()` type-checks.
import 'vitest'
import type { AxeMatchers } from 'vitest-axe/matchers'

declare module 'vitest' {
  interface Assertion<T = any> extends AxeMatchers {}
  interface AsymmetricMatchersContaining extends AxeMatchers {}
}
