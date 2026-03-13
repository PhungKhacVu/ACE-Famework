import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { createEventBus } from '../src/events.ts';

type TestEvents = {
  greet: string;
  count: number;
  empty: undefined;
};

describe('createEventBus', () => {
  it('calls a registered handler when the event is emitted', () => {
    const bus = createEventBus<TestEvents>();
    const received: string[] = [];
    bus.on('greet', name => received.push(name));
    bus.emit('greet', 'Alice');
    assert.deepEqual(received, ['Alice']);
  });

  it('calls multiple handlers in registration order', () => {
    const bus = createEventBus<TestEvents>();
    const order: string[] = [];
    bus.on('greet', () => order.push('first'));
    bus.on('greet', () => order.push('second'));
    bus.emit('greet', 'Bob');
    assert.deepEqual(order, ['first', 'second']);
  });

  it('passes the correct payload', () => {
    const bus = createEventBus<TestEvents>();
    let received = 0;
    bus.on('count', n => (received = n));
    bus.emit('count', 99);
    assert.equal(received, 99);
  });

  it('unsubscribes via the returned function', () => {
    const bus = createEventBus<TestEvents>();
    const calls: string[] = [];
    const unsub = bus.on('greet', v => calls.push(v));
    bus.emit('greet', 'first');
    unsub();
    bus.emit('greet', 'second');
    assert.deepEqual(calls, ['first']);
  });

  it('off(event) removes all handlers for that event', () => {
    const bus = createEventBus<TestEvents>();
    const calls: string[] = [];
    bus.on('greet', v => calls.push(v));
    bus.on('greet', v => calls.push(v.toUpperCase()));
    bus.off('greet');
    bus.emit('greet', 'hello');
    assert.deepEqual(calls, []);
  });

  it('off() with no argument removes all handlers for all events', () => {
    const bus = createEventBus<TestEvents>();
    const greetCalls: string[] = [];
    const countCalls: number[] = [];
    bus.on('greet', v => greetCalls.push(v));
    bus.on('count', v => countCalls.push(v));
    bus.off();
    bus.emit('greet', 'hello');
    bus.emit('count', 1);
    assert.deepEqual(greetCalls, []);
    assert.deepEqual(countCalls, []);
  });

  it('handlers added during emit are not called in the same round', () => {
    const bus = createEventBus<TestEvents>();
    const calls: string[] = [];
    bus.on('greet', () => {
      bus.on('greet', v => calls.push('late:' + v));
    });
    bus.emit('greet', 'first');
    assert.deepEqual(calls, []); // late handler not called yet
    bus.emit('greet', 'second');
    assert.deepEqual(calls, ['late:second']);
  });

  it('does not throw when emitting to an event with no handlers', () => {
    const bus = createEventBus<TestEvents>();
    assert.doesNotThrow(() => bus.emit('greet', 'nobody'));
  });

  it('does not throw when off() is called for an event with no handlers', () => {
    const bus = createEventBus<TestEvents>();
    assert.doesNotThrow(() => bus.off('greet'));
  });
});
