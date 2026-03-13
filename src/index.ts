/**
 * ACE Framework — public API
 *
 * Adaptive Component Engine: a lightweight, TypeScript-first framework for
 * building modular, component-based web applications.
 */

// State
export { signal } from './state.js';
export type { Signal } from './state.js';

// Events
export { createEventBus } from './events.js';
export type { EventBus } from './events.js';

// Renderer
export { render } from './renderer.js';
export type { RenderContext } from './renderer.js';

// Component
export { defineComponent } from './component.js';
export type { ComponentOptions, ComponentInstance, ComponentConstructor } from './component.js';

// Plugin / App
export { createApp } from './plugin.js';
export type { AceApp, AcePlugin } from './plugin.js';
