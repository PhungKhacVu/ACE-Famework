import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../src/plugin.ts';
import type { AcePlugin } from '../src/plugin.ts';

describe('createApp', () => {
  it('creates an app with use(), component(), mount(), and unmount() methods', () => {
    const app = createApp({ name: 'Root', template: '' });
    assert.equal(typeof app.use, 'function');
    assert.equal(typeof app.component, 'function');
    assert.equal(typeof app.mount, 'function');
    assert.equal(typeof app.unmount, 'function');
  });

  it('installs a plugin by calling its install() function', () => {
    let installed = false;
    const plugin: AcePlugin = {
      name: 'TestPlugin',
      install() {
        installed = true;
      },
    };
    const app = createApp({ name: 'Root', template: '' });
    app.use(plugin);
    assert.equal(installed, true);
  });

  it('passes options to the plugin install() function', () => {
    let receivedOptions: Record<string, unknown> | undefined;
    const plugin: AcePlugin = {
      name: 'OptionsPlugin',
      install(_app, opts) {
        receivedOptions = opts;
      },
    };
    const app = createApp({ name: 'Root', template: '' });
    app.use(plugin, { key: 'value' });
    assert.deepEqual(receivedOptions, { key: 'value' });
  });

  it('warns and skips a plugin installed twice', () => {
    const warnings: string[] = [];
    const original = console.warn;
    console.warn = (msg: string) => warnings.push(msg);

    const plugin: AcePlugin = {
      name: 'DupePlugin',
      install() {},
    };
    const app = createApp({ name: 'Root', template: '' });
    app.use(plugin);
    app.use(plugin); // second call — should warn
    console.warn = original;

    assert.equal(warnings.length, 1);
    assert.ok(warnings[0].includes('DupePlugin'));
  });

  it('returns the app for chaining from use()', () => {
    const plugin: AcePlugin = { name: 'Chain', install() {} };
    const app = createApp({ name: 'Root', template: '' });
    const returned = app.use(plugin);
    assert.equal(returned, app);
  });

  it('returns the app for chaining from component()', () => {
    const app = createApp({ name: 'Root', template: '' });
    const returned = app.component('Foo', { name: 'Foo', template: '' });
    assert.equal(returned, app);
  });

  it('unmount() does not throw when called after mount()', () => {
    const app = createApp({ name: 'Root', template: '' });
    app.mount('');   // no DOM in Node — no-op path
    assert.doesNotThrow(() => app.unmount());
  });
});
