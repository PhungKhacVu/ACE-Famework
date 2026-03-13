/**
 * Lightweight string-interpolation renderer.
 *
 * Supported syntax:
 *   - {{ key }}            — interpolate a value from the context
 *   - ace-if="expr"        — conditionally render an element
 *   - ace-each="x in list" — render an element once per item in an array
 */

export type RenderContext = Record<string, unknown>;

const MAX_DEPTH = 10;

/**
 * Renders a template string using the provided context object.
 * Returns an HTML string.
 *
 * @example
 * render('<p>{{ name }}</p>', { name: 'Alice' }); // '<p>Alice</p>'
 */
export function render(template: string, ctx: RenderContext, _depth = 0): string {
  if (_depth > MAX_DEPTH) return template;

  let result = template;

  // Process ace-each directives first (outermost match only, then recurse).
  result = processEach(result, ctx, _depth);

  // Process ace-if directives.
  result = processIf(result, ctx, _depth);

  // Process {{ interpolations }}.
  result = interpolate(result, ctx);

  return result;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Evaluates a simple expression against the context.
 * Supports:
 *   - plain key lookup  (e.g. `visible`)
 *   - negation          (e.g. `!visible`)
 */
function evaluate(expr: string, ctx: RenderContext): unknown {
  const trimmed = expr.trim();
  if (trimmed.startsWith('!')) {
    return !ctx[trimmed.slice(1).trim()];
  }
  return ctx[trimmed];
}

/**
 * Replaces `{{ key }}` placeholders with their context values.
 * Unknown keys render as empty string.
 */
function interpolate(template: string, ctx: RenderContext): string {
  return template.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_match, key: string) => {
    const value = ctx[key];
    return value == null ? '' : String(value);
  });
}

/**
 * Processes ace-if directives.
 *
 * Matches elements of the form:
 *   <tag ... ace-if="expr" ...>...</tag>
 *
 * The element is kept (with the attribute removed) when the expression is
 * truthy, and removed entirely when falsy.
 */
function processIf(template: string, ctx: RenderContext, depth: number): string {
  // Matches a single opening tag that contains ace-if="…"
  const ifPattern = /<(\w+)([^>]*?)\s+ace-if="([^"]+)"([^>]*)>([\s\S]*?)<\/\1>/g;

  return template.replace(
    ifPattern,
    (_match, tag: string, before: string, expr: string, after: string, inner: string) => {
      const condition = evaluate(expr, ctx);
      if (!condition) return '';
      const cleaned = `<${tag}${before}${after}>${inner}</${tag}>`;
      return render(cleaned, ctx, depth + 1);
    },
  );
}

/**
 * Processes ace-each directives.
 *
 * Matches elements of the form:
 *   <tag ... ace-each="item in list" ...>...</tag>
 *
 * Repeats the element once per item; within each iteration the context is
 * augmented with the loop variable.
 */
function processEach(template: string, ctx: RenderContext, depth: number): string {
  const eachPattern = /<(\w+)([^>]*?)\s+ace-each="(\w+)\s+in\s+(\w+)"([^>]*)>([\s\S]*?)<\/\1>/g;

  return template.replace(
    eachPattern,
    (
      _match,
      tag: string,
      before: string,
      itemVar: string,
      listKey: string,
      after: string,
      inner: string,
    ) => {
      const list = ctx[listKey];
      if (!Array.isArray(list)) return '';

      return list
        .map((item: unknown) => {
          const itemCtx: RenderContext = { ...ctx, [itemVar]: item };
          const cleaned = `<${tag}${before}${after}>${inner}</${tag}>`;
          return render(cleaned, itemCtx, depth + 1);
        })
        .join('');
    },
  );
}
