// Phase C1 — prove Vitest can discover and run tests in this project.
import { describe, it, expect } from 'vitest';

describe('vitest bootstrap', () => {
  it('runs', () => {
    expect(1 + 1).toBe(2);
  });
});
