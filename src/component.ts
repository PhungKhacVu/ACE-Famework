import { signal } from './state.js';
import { render, type RenderContext } from './renderer.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ComponentOptions<Props extends Record<string, unknown> = Record<string, unknown>> {
  /** Unique display name used in error messages and dev-tools. */
  name: string;
  /** Default prop values. Merged with props passed at construction time. */
  props?: Partial<Props>;
  /**
   * Setup function that returns additional reactive context to expose to
   * the template. Receives the initial (merged) props.
   */
  setup?: (props: Props) => Record<string, unknown>;
  /** Template string or function that returns an HTML string. */
  template: string | ((ctx: RenderContext) => string);
  /** Lifecycle hooks. */
  hooks?: {
    onMount?: () => void;
    onUnmount?: () => void;
    onUpdate?: (prevProps: Props, nextProps: Props) => void;
  };
}

export interface ComponentInstance<Props extends Record<string, unknown> = Record<string, unknown>> {
  readonly name: string;
  /** Current props. Setting this triggers an update. */
  props: Props;
  /** Merge new props and re-render the component. */
  update(newProps?: Partial<Props>): void;
  /**
   * Mount the component into `target`.
   * In a browser environment `target` may be a CSS selector string or an
   * Element; in Node/test environments only the string form is used to
   * simulate rendering (the HTML is returned by the internal render call).
   */
  mount(target: Element | string): void;
  /** Unmount the component and invoke the onUnmount hook. */
  unmount(): void;
  /** Returns the last rendered HTML string (useful for testing / SSR). */
  readonly html: string;
}

export type ComponentConstructor<Props extends Record<string, unknown>> = new (
  props?: Partial<Props>,
) => ComponentInstance<Props>;

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

/**
 * Defines a new component class according to the given options.
 *
 * @example
 * const Greeting = defineComponent({
 *   name: 'Greeting',
 *   props: { name: 'World' },
 *   template: '<h1>Hello, {{ name }}!</h1>',
 * });
 * const instance = new Greeting({ name: 'Alice' });
 * instance.mount('#app');
 */
export function defineComponent<Props extends Record<string, unknown> = Record<string, unknown>>(
  options: ComponentOptions<Props>,
): ComponentConstructor<Props> {
  return class Component implements ComponentInstance<Props> {
    readonly name: string;

    private _propsSignal: ReturnType<typeof signal<Props>>;
    private _mounted = false;
    private _target: Element | null = null;
    private _html = '';
    private _setupCtx: Record<string, unknown> = {};

    constructor(initProps?: Partial<Props>) {
      this.name = options.name;

      // Merge default props with instance props.
      const merged = { ...(options.props ?? {}), ...(initProps ?? {}) } as Props;
      this._propsSignal = signal<Props>(merged);

      // Run setup if provided.
      if (options.setup) {
        this._setupCtx = options.setup(merged);
      }
    }

    get props(): Props {
      return this._propsSignal.value;
    }

    set props(newProps: Props) {
      this.update(newProps);
    }

    update(newProps?: Partial<Props>): void {
      const prev = this._propsSignal.value;
      const next = newProps ? ({ ...prev, ...newProps } as Props) : prev;
      this._propsSignal.set(next);
      this._render();
      if (this._mounted) {
        options.hooks?.onUpdate?.(prev, next);
      }
    }

    mount(target: Element | string): void {
      if (this._mounted) {
        throw new Error(`[ACE] Component "${this.name}" is already mounted.`);
      }

      // Resolve target element in browser environments.
      if (typeof target === 'string') {
        if (typeof document !== 'undefined') {
          const el = document.querySelector(target);
          if (!el) throw new Error(`[ACE] Mount target "${target}" not found.`);
          this._target = el;
        }
        // In non-browser environments (Node/tests) we skip DOM manipulation.
      } else {
        this._target = target;
      }

      this._render();
      this._mounted = true;
      options.hooks?.onMount?.();
    }

    unmount(): void {
      if (this._target) {
        this._target.innerHTML = '';
        this._target = null;
      }
      this._mounted = false;
      options.hooks?.onUnmount?.();
    }

    get html(): string {
      return this._html;
    }

    private _render(): void {
      const ctx: RenderContext = {
        ...this._propsSignal.value,
        ...this._setupCtx,
      };

      const tmpl = options.template;
      const raw = typeof tmpl === 'function' ? tmpl(ctx) : tmpl;
      this._html = render(raw, ctx);

      if (this._target) {
        this._target.innerHTML = this._html;
      }
    }
  };
}
