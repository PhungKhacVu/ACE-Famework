# ACE Framework — Technical Software Specification

## 1. Overview

**ACE** (Adaptive Component Engine) is a lightweight, TypeScript-first framework for building modular,
component-based web applications. It aims to provide a minimal yet powerful set of primitives—
components, reactive state, an event bus, and a plugin system—without imposing a specific build
pipeline or view library.

### Goals
- Zero external runtime dependencies.
- < 5 KB minified + gzipped core bundle.
- Full TypeScript support with strict typings.
- Works in modern browsers (ES2018+) and Node.js 18+.
- Easily extensible via a first-class plugin API.

### Non-Goals
- Does not replace React, Vue, or Angular.
- Does not include a router or HTTP client in the core.
- Does not require a bundler (ships as ES modules).

---

## 2. Architecture

```
ace/
├── src/
│   ├── component.ts     # Component definition & lifecycle
│   ├── state.ts         # Reactive state (signals)
│   ├── events.ts        # Typed event bus
│   ├── renderer.ts      # Lightweight template renderer
│   ├── plugin.ts        # Plugin system
│   └── index.ts         # Public API barrel
├── tests/
│   ├── component.test.ts
│   ├── state.test.ts
│   ├── events.test.ts
│   ├── renderer.test.ts
│   └── plugin.test.ts
├── package.json
├── tsconfig.json
└── SPEC.md
```

### Module dependency graph

```
index.ts
  ├── component.ts  ──► state.ts
  │                 ──► events.ts
  │                 ──► renderer.ts
  ├── state.ts
  ├── events.ts
  ├── renderer.ts
  └── plugin.ts     ──► (receives ace instance)
```

---

## 3. Module Specifications

### 3.1 State Module (`state.ts`)

Provides a **signal**-based reactive primitive. A *signal* holds a value and notifies
subscribers whenever it changes.

#### API

```ts
/** Creates a reactive signal. */
function signal<T>(initialValue: T): Signal<T>;

interface Signal<T> {
  /** Read the current value. */
  get value(): T;
  /** Write a new value and notify all subscribers. */
  set value(newValue: T);
  /** Register a callback invoked on every value change. Returns an unsubscribe fn. */
  subscribe(cb: (value: T) => void): () => void;
}
```

#### Behavior
- Setting `.value` to the **same** reference (strict equality) must **not** trigger subscribers.
- Subscribers are called synchronously in the order they were registered.
- The returned unsubscribe function removes the subscriber; calling it more than once is a no-op.

---

### 3.2 Event Bus Module (`events.ts`)

A typed publish/subscribe bus that decouples components.

#### API

```ts
/** Creates an isolated event bus. */
function createEventBus<Events extends Record<string, unknown>>(): EventBus<Events>;

interface EventBus<Events extends Record<string, unknown>> {
  /** Subscribe to an event. Returns an unsubscribe function. */
  on<K extends keyof Events>(event: K, handler: (payload: Events[K]) => void): () => void;
  /** Publish an event to all subscribers. */
  emit<K extends keyof Events>(event: K, payload: Events[K]): void;
  /** Remove all handlers for a specific event (or all events if omitted). */
  off<K extends keyof Events>(event?: K): void;
}
```

#### Behavior
- Handlers are called in registration order.
- Handlers added **during** an emit are **not** called until the next emit.
- `off()` with no argument clears every registered handler.

---

### 3.3 Component Module (`component.ts`)

Components are the building blocks of an ACE application. Each component is a self-contained
unit with its own state, lifecycle hooks, and template.

#### API

```ts
/** Defines a new component class. */
function defineComponent<Props extends Record<string, unknown> = Record<string, unknown>>(
  options: ComponentOptions<Props>
): ComponentConstructor<Props>;

interface ComponentOptions<Props> {
  /** Unique name used for debugging and the plugin registry. */
  name: string;
  /** Initial prop values (validated at construction). */
  props?: Partial<Props>;
  /** Factory that returns the component's reactive state. */
  setup?: (props: Props) => Record<string, unknown>;
  /** Template string or render function. */
  template: string | ((ctx: RenderContext) => string);
  /** Lifecycle hooks. */
  hooks?: {
    onMount?: () => void;
    onUnmount?: () => void;
    onUpdate?: (prevProps: Props, nextProps: Props) => void;
  };
}

interface ComponentInstance<Props> {
  readonly name: string;
  props: Props;
  /** Trigger a re-render. */
  update(newProps?: Partial<Props>): void;
  /** Attach the component to a DOM element (browser) or return HTML string (SSR). */
  mount(target: Element | string): void;
  /** Detach the component and run onUnmount. */
  unmount(): void;
}
```

#### Lifecycle

```
defineComponent() → new Instance() → mount() → [update()* ] → unmount()
                                         │
                                    onMount hook
```

#### Behavior
- `mount(target)` calls `onMount` after the first render.
- `update(newProps)` merges `newProps` into current props, re-renders, and calls `onUpdate`.
- `unmount()` calls `onUnmount` and removes the rendered HTML from the target.
- Calling `mount()` on an already-mounted component throws an error.

---

### 3.4 Renderer Module (`renderer.ts`)

A minimal string-interpolation renderer. Supports `{{ expression }}` placeholders and
`ace-if` / `ace-each` directives.

#### API

```ts
/**
 * Renders a template string using the provided context.
 * Returns an HTML string.
 */
function render(template: string, ctx: RenderContext): string;

type RenderContext = Record<string, unknown>;
```

#### Template syntax

| Feature | Syntax | Example |
|---------|--------|---------|
| Interpolation | `{{ key }}` | `<p>{{ name }}</p>` |
| Conditional | `<tag ace-if="expr">…</tag>` | `<span ace-if="visible">Hi</span>` |
| List | `<tag ace-each="item in list">…</tag>` | `<li ace-each="x in items">{{ x }}</li>` |

#### Behavior
- Unknown keys in `{{ … }}` render as an empty string.
- Nested directives are supported to a depth of 10 (prevents runaway recursion).
- HTML output is **not** sanitized by default; callers are responsible for escaping user data.

---

### 3.5 Plugin Module (`plugin.ts`)

Plugins extend the ACE instance with new capabilities (e.g., router, HTTP client, i18n).

#### API

```ts
/** The top-level ACE application instance. */
interface AceApp {
  use(plugin: AcePlugin, options?: Record<string, unknown>): this;
  component<P>(name: string, options: ComponentOptions<P>): this;
  mount(selector: string): void;
}

interface AcePlugin {
  name: string;
  install(app: AceApp, options?: Record<string, unknown>): void;
}

/** Creates an ACE application. */
function createApp(rootOptions: ComponentOptions<Record<string, unknown>>): AceApp;
```

#### Behavior
- Each plugin may only be installed once per app; a second `use()` call with the same plugin is a no-op with a console warning.
- `app.component()` registers a global component reusable across templates.
- `app.mount(selector)` mounts the root component into the matching DOM element.

---

## 4. Public API Surface (`index.ts`)

```ts
export { signal }          from './state';
export { createEventBus }  from './events';
export { defineComponent } from './component';
export { render }          from './renderer';
export { createApp }       from './plugin';
export type {
  Signal,
  EventBus,
  ComponentOptions,
  ComponentInstance,
  RenderContext,
  AceApp,
  AcePlugin,
} from './*';
```

---

## 5. Build & Tooling

| Tool | Purpose |
|------|---------|
| TypeScript 5.x | Language |
| tsx | Zero-config TS execution (dev/test) |
| Node.js built-in test runner (`node:test`) | Unit tests |
| `tsc` | Production build to `dist/` (ESM + CJS + `.d.ts`) |

### Scripts

```jsonc
{
  "scripts": {
    "build":  "tsc",
    "test":   "node --import tsx/esm --test tests/**/*.test.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

---

## 6. Testing Strategy

Each module has a dedicated test file in `tests/`. Tests use the Node.js built-in runner
(`node:test` + `assert`). Coverage targets:

| Module | Target |
|--------|--------|
| state | 100% |
| events | 100% |
| renderer | 95% |
| component | 90% |
| plugin | 90% |

---

## 7. Implementation Steps

1. **Scaffold** — `package.json`, `tsconfig.json`, `.gitignore`.
2. **State** — Implement `signal()` with strict-equality guard and subscriber management.
3. **Events** — Implement `createEventBus()` with snapshot-on-emit semantics.
4. **Renderer** — Implement `render()` with interpolation, `ace-if`, `ace-each`.
5. **Component** — Implement `defineComponent()` backed by signal-driven re-render.
6. **Plugin / App** — Implement `createApp()` + plugin registry.
7. **Barrel** — Export everything from `index.ts`.
8. **Tests** — Write and pass tests for all modules.
9. **README** — Document installation and quick-start usage.
