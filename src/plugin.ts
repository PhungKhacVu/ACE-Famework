import { defineComponent, type ComponentOptions } from './component.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AcePlugin {
  /** Unique plugin name. Used to guard against double-installation. */
  name: string;
  /** Called once when the plugin is installed. */
  install(app: AceApp, options?: Record<string, unknown>): void;
}

export interface AceApp {
  /**
   * Install a plugin.
   * Calling `use()` with the same plugin more than once is a no-op
   * (a warning is logged to the console).
   */
  use(plugin: AcePlugin, options?: Record<string, unknown>): this;
  /**
   * Register a global component by name so that it can be referenced
   * within other templates (future router / portal support).
   */
  component<P extends Record<string, unknown>>(name: string, options: ComponentOptions<P>): this;
  /**
   * Mount the root component into the DOM element matching `selector`.
   * Throws if the element is not found.
   */
  mount(selector: string): void;
  /** Unmount the root component. */
  unmount(): void;
}

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

/**
 * Creates an ACE application with the given root component options.
 *
 * @example
 * const app = createApp({
 *   name: 'App',
 *   template: '<h1>Hello, {{ name }}!</h1>',
 *   props: { name: 'World' },
 * });
 * app.mount('#app');
 */
export function createApp(
  rootOptions: ComponentOptions<Record<string, unknown>>,
): AceApp {
  const installedPlugins = new Set<string>();
  const globalComponents = new Map<string, ComponentOptions<Record<string, unknown>>>();

  const RootComponent = defineComponent(rootOptions);
  const root = new RootComponent();

  const app: AceApp = {
    use(plugin: AcePlugin, options?: Record<string, unknown>): AceApp {
      if (installedPlugins.has(plugin.name)) {
        console.warn(`[ACE] Plugin "${plugin.name}" is already installed. Skipping.`);
        return app;
      }
      plugin.install(app, options);
      installedPlugins.add(plugin.name);
      return app;
    },

    component<P extends Record<string, unknown>>(
      name: string,
      options: ComponentOptions<P>,
    ): AceApp {
      globalComponents.set(name, options as ComponentOptions<Record<string, unknown>>);
      return app;
    },

    mount(selector: string): void {
      root.mount(selector);
    },

    unmount(): void {
      root.unmount();
    },
  };

  return app;
}
