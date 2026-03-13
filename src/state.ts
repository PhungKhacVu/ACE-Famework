/**
 * Signal — a reactive value container.
 *
 * A signal holds a value and notifies registered subscribers whenever
 * that value changes (using strict equality to detect changes).
 */
export interface Signal<T> {
  /** Read the current value. */
  readonly value: T;
  /** Write a new value. Notifies subscribers only when the value has changed. */
  set(newValue: T): void;
  /** Register a callback invoked on every value change. Returns an unsubscribe function. */
  subscribe(cb: (value: T) => void): () => void;
}

/**
 * Creates a new reactive signal with the given initial value.
 *
 * @example
 * const count = signal(0);
 * count.subscribe(v => console.log('count =', v));
 * count.set(1); // logs: count = 1
 */
export function signal<T>(initialValue: T): Signal<T> {
  let current = initialValue;
  const subscribers = new Set<(value: T) => void>();

  return {
    get value(): T {
      return current;
    },

    set(newValue: T): void {
      if (newValue === current) return;
      current = newValue;
      // Snapshot the set before iterating so that subscribers added during
      // notification are not called in the current round.
      for (const cb of [...subscribers]) {
        cb(current);
      }
    },

    subscribe(cb: (value: T) => void): () => void {
      subscribers.add(cb);
      return () => {
        subscribers.delete(cb);
      };
    },
  };
}
