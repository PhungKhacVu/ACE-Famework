import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { defineComponent } from '../src/component.ts';

describe('defineComponent', () => {
  it('creates a component instance with the correct name', () => {
    const Comp = defineComponent({ name: 'MyComp', template: '' });
    const inst = new Comp();
    assert.equal(inst.name, 'MyComp');
  });

  it('merges default props with instance props', () => {
    const Comp = defineComponent({
      name: 'Greeter',
      props: { name: 'World', count: 0 },
      template: '',
    });
    const inst = new Comp({ name: 'Alice' });
    assert.equal(inst.props.name, 'Alice');
    assert.equal(inst.props.count, 0);
  });

  it('renders the template using props', () => {
    const Comp = defineComponent({
      name: 'Hello',
      props: { name: 'World' },
      template: '<h1>Hello, {{ name }}!</h1>',
    });
    const inst = new Comp({ name: 'ACE' });
    // mount without a DOM target — html is produced but no DOM mutation
    inst.mount('');
    assert.equal(inst.html, '<h1>Hello, ACE!</h1>');
  });

  it('update() changes props and re-renders', () => {
    const Comp = defineComponent({
      name: 'Counter',
      props: { count: 0 },
      template: '<span>{{ count }}</span>',
    });
    const inst = new Comp();
    inst.mount('');
    inst.update({ count: 5 });
    assert.equal(inst.html, '<span>5</span>');
  });

  it('calls onMount hook after first render', () => {
    let mounted = false;
    const Comp = defineComponent({
      name: 'Hooks',
      template: '',
      hooks: { onMount: () => (mounted = true) },
    });
    const inst = new Comp();
    assert.equal(mounted, false);
    inst.mount('');
    assert.equal(mounted, true);
  });

  it('calls onUnmount hook when unmounted', () => {
    let unmounted = false;
    const Comp = defineComponent({
      name: 'Hooks',
      template: '',
      hooks: { onUnmount: () => (unmounted = true) },
    });
    const inst = new Comp();
    inst.mount('');
    inst.unmount();
    assert.equal(unmounted, true);
  });

  it('calls onUpdate hook with prev and next props', () => {
    const updates: Array<{ prev: Record<string, unknown>; next: Record<string, unknown> }> = [];
    const Comp = defineComponent({
      name: 'Updater',
      props: { val: 'a' },
      template: '',
      hooks: {
        onUpdate: (prev, next) => updates.push({ prev, next }),
      },
    });
    const inst = new Comp();
    inst.mount('');
    inst.update({ val: 'b' });
    assert.equal(updates.length, 1);
    assert.equal(updates[0].prev.val, 'a');
    assert.equal(updates[0].next.val, 'b');
  });

  it('throws when mounted twice', () => {
    const Comp = defineComponent({ name: 'Double', template: '' });
    const inst = new Comp();
    inst.mount('');
    assert.throws(() => inst.mount(''), /already mounted/);
  });

  it('exposes setup() context in the template', () => {
    const Comp = defineComponent({
      name: 'Setup',
      props: { base: 10 },
      setup: props => ({ doubled: (props.base as number) * 2 }),
      template: '<p>{{ doubled }}</p>',
    });
    const inst = new Comp({ base: 7 });
    inst.mount('');
    assert.equal(inst.html, '<p>14</p>');
  });

  it('supports a render function as template', () => {
    const Comp = defineComponent({
      name: 'FnTemplate',
      props: { x: 1 },
      template: ctx => `<b>${(ctx.x as number) * 3}</b>`,
    });
    const inst = new Comp({ x: 5 });
    inst.mount('');
    assert.equal(inst.html, '<b>15</b>');
  });
});
