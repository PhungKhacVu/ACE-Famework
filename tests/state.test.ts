import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { signal } from '../src/state.ts';

describe('signal', () => {
  it('returns the initial value', () => {
    const s = signal(42);
    assert.equal(s.value, 42);
  });

  it('updates the value via set()', () => {
    const s = signal('hello');
    s.set('world');
    assert.equal(s.value, 'world');
  });

  it('notifies subscribers on change', () => {
    const s = signal(0);
    const calls: number[] = [];
    s.subscribe(v => calls.push(v));
    s.set(1);
    s.set(2);
    assert.deepEqual(calls, [1, 2]);
  });

  it('does NOT notify when the value is the same reference', () => {
    const s = signal(10);
    let count = 0;
    s.subscribe(() => count++);
    s.set(10); // same value
    assert.equal(count, 0);
  });

  it('allows multiple independent subscribers', () => {
    const s = signal('a');
    const out1: string[] = [];
    const out2: string[] = [];
    s.subscribe(v => out1.push(v));
    s.subscribe(v => out2.push(v));
    s.set('b');
    assert.deepEqual(out1, ['b']);
    assert.deepEqual(out2, ['b']);
  });

  it('unsubscribes cleanly', () => {
    const s = signal(0);
    const calls: number[] = [];
    const unsub = s.subscribe(v => calls.push(v));
    s.set(1);
    unsub();
    s.set(2);
    assert.deepEqual(calls, [1]); // second change not received
  });

  it('calling unsubscribe twice is a no-op', () => {
    const s = signal(0);
    const unsub = s.subscribe(() => {});
    unsub();
    assert.doesNotThrow(() => unsub());
  });

  it('subscribers added during notify are not called in the same round', () => {
    const s = signal(0);
    const calls: number[] = [];
    s.subscribe(() => {
      s.subscribe(v => calls.push(v)); // added mid-notification
    });
    s.set(1);
    // The newly added subscriber should NOT have been called yet.
    assert.deepEqual(calls, []);
    s.set(2);
    // Now it is called.
    assert.deepEqual(calls, [2]);
  });
});
