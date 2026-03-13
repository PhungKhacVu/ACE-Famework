/**
 * Typed publish/subscribe event bus.
 *
 * The generic `Events` parameter maps event names to their payload types,
 * giving full type safety at the call-site.
 *
 * @example
 * type MyEvents = { greet: string; count: number };
 * const bus = createEventBus<MyEvents>();
 * bus.on('greet', name => console.log('Hello', name));
 * bus.emit('greet', 'World'); // logs: Hello World
 */
export interface EventBus<Events extends Record<string, unknown>> {
  /** Subscribe to an event. Returns an unsubscribe function. */
  on<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): () => void;
  /** Publish an event to all current subscribers. */
  emit<K extends keyof Events>(event: K, payload: Events[K]): void;
  /**
   * Remove handlers.
   * - If `event` is provided, removes all handlers for that event.
   * - If `event` is omitted, removes **all** handlers for every event.
   */
  off<K extends keyof Events>(event?: K): void;
}

/**
 * Creates an isolated, typed event bus.
 */
export function createEventBus<
  Events extends Record<string, unknown> = Record<string, unknown>,
>(): EventBus<Events> {
  type Handler = (payload: unknown) => void;
  const registry = new Map<keyof Events, Set<Handler>>();

  function getHandlers(event: keyof Events): Set<Handler> {
    let set = registry.get(event);
    if (!set) {
      set = new Set();
      registry.set(event, set);
    }
    return set;
  }

  return {
    on<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): () => void {
      const handlers = getHandlers(event);
      const h = handler as Handler;
      handlers.add(h);
      return () => {
        handlers.delete(h);
      };
    },

    emit<K extends keyof Events>(event: K, payload: Events[K]): void {
      const handlers = getHandlers(event);
      // Snapshot handlers before iterating so that handlers added during
      // emit are not invoked until the next emit.
      for (const h of [...handlers]) {
        h(payload);
      }
    },

    off<K extends keyof Events>(event?: K): void {
      if (event === undefined) {
        registry.clear();
      } else {
        registry.delete(event);
      }
    },
  };
}
