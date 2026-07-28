import { useEffect, useState, type Dispatch, type SetStateAction } from 'react';

/**
 * Persists React state in sessionStorage so it survives route changes within the app
 * (same tab). Survives refresh; cleared when the tab closes.
 */
export function useSessionStorageState<T>(
  key: string,
  defaultValue: T,
  merge?: (saved: Partial<T>, def: T) => T,
): [T, Dispatch<SetStateAction<T>>] {
  const [state, setState] = useState<T>(() => {
    try {
      const raw = sessionStorage.getItem(key);
      if (!raw) return defaultValue;
      const parsed = JSON.parse(raw) as Partial<T>;
      if (merge) return merge(parsed, defaultValue);
      if (
        parsed &&
        typeof parsed === 'object' &&
        !Array.isArray(parsed) &&
        defaultValue !== null &&
        typeof defaultValue === 'object' &&
        !Array.isArray(defaultValue)
      ) {
        return { ...(defaultValue as object), ...(parsed as object) } as T;
      }
      return parsed as T;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(key, JSON.stringify(state));
    } catch {
      /* quota / private mode */
    }
  }, [key, state]);

  return [state, setState];
}
