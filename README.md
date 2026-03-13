# ACE Framework

**Adaptive Component Engine** — a lightweight, TypeScript-first framework for building modular,
component-based web applications.

- ✅ Zero external runtime dependencies
- ✅ Full TypeScript support with strict typings
- ✅ Reactive state (signals), typed event bus, template renderer, plugin system
- ✅ Works in modern browsers (ES2018+) and Node.js 18+
- ✅ < 5 KB core (minified + gzip target)

See [SPEC.md](./SPEC.md) for the full technical specification.

---

## Quick start

```bash
npm install ace-framework
```

```ts
import { createApp } from 'ace-framework';

const app = createApp({
  name: 'App',
  props: { name: 'World' },
  template: '<h1>Hello, {{ name }}!</h1>',
});

app.mount('#app');
```

---

## Core modules

### `signal` — reactive state

```ts
import { signal } from 'ace-framework';

const count = signal(0);
count.subscribe(v => console.log('count =', v));
count.set(1); // logs: count = 1
```

### `createEventBus` — typed pub/sub

```ts
import { createEventBus } from 'ace-framework';

type Events = { greet: string };
const bus = createEventBus<Events>();
bus.on('greet', name => console.log('Hello,', name));
bus.emit('greet', 'Alice'); // logs: Hello, Alice
```

### `render` — template renderer

```ts
import { render } from 'ace-framework';

render('<p>{{ name }}</p>', { name: 'Bob' });
// => '<p>Bob</p>'

render('<li ace-each="x in items">{{ x }}</li>', { items: ['a', 'b', 'c'] });
// => '<li>a</li><li>b</li><li>c</li>'
```

### `defineComponent` — component system

```ts
import { defineComponent } from 'ace-framework';

const Greeting = defineComponent({
  name: 'Greeting',
  props: { name: 'World' },
  template: '<h1>Hello, {{ name }}!</h1>',
  hooks: {
    onMount: () => console.log('mounted!'),
  },
});

const instance = new Greeting({ name: 'Alice' });
instance.mount('#app');
instance.update({ name: 'Bob' });
instance.unmount();
```

### `createApp` — application & plugin system

```ts
import { createApp } from 'ace-framework';
import type { AcePlugin } from 'ace-framework';

const myPlugin: AcePlugin = {
  name: 'MyPlugin',
  install(app, options) {
    console.log('plugin installed with', options);
  },
};

const app = createApp({ name: 'Root', template: '<div>{{ title }}</div>', props: { title: 'ACE' } });
app.use(myPlugin, { debug: true });
app.mount('#app');
```

---

## Development

```bash
npm test        # run all tests (node:test + tsx)
npm run build   # compile to dist/ (ESM + CJS)
npm run typecheck  # type-check without emitting
```