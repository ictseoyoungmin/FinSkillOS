/**
 * Conditionally join class names. Mirrors the `clsx` API without adding a
 * dependency — only handles strings / falsy values which is all the OS
 * shell needs.
 */
export function cn(...inputs: Array<string | false | null | undefined>): string {
  return inputs.filter(Boolean).join(" ");
}
