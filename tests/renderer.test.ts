import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { render } from '../src/renderer.ts';

describe('render — interpolation', () => {
  it('replaces {{ key }} with the context value', () => {
    assert.equal(render('<p>{{ name }}</p>', { name: 'Alice' }), '<p>Alice</p>');
  });

  it('replaces multiple placeholders', () => {
    assert.equal(
      render('{{ greeting }}, {{ name }}!', { greeting: 'Hello', name: 'Bob' }),
      'Hello, Bob!',
    );
  });

  it('renders empty string for unknown keys', () => {
    assert.equal(render('{{ missing }}', {}), '');
  });

  it('renders 0 and false correctly', () => {
    assert.equal(render('{{ count }}', { count: 0 }), '0');
    assert.equal(render('{{ flag }}', { flag: false }), 'false');
  });

  it('renders null/undefined as empty string', () => {
    assert.equal(render('{{ x }}', { x: null }), '');
    assert.equal(render('{{ x }}', { x: undefined }), '');
  });
});

describe('render — ace-if directive', () => {
  it('renders element when condition is truthy', () => {
    assert.equal(
      render('<span ace-if="visible">Hi</span>', { visible: true }),
      '<span>Hi</span>',
    );
  });

  it('removes element when condition is falsy', () => {
    assert.equal(render('<span ace-if="visible">Hi</span>', { visible: false }), '');
  });

  it('supports negation with !', () => {
    assert.equal(
      render('<span ace-if="!hidden">Shown</span>', { hidden: false }),
      '<span>Shown</span>',
    );
    assert.equal(render('<span ace-if="!hidden">Shown</span>', { hidden: true }), '');
  });

  it('interpolates inner content after ace-if is resolved', () => {
    assert.equal(
      render('<p ace-if="show">{{ msg }}</p>', { show: true, msg: 'hello' }),
      '<p>hello</p>',
    );
  });
});

describe('render — ace-each directive', () => {
  it('renders one element per item', () => {
    const result = render('<li ace-each="item in items">{{ item }}</li>', {
      items: ['a', 'b', 'c'],
    });
    assert.equal(result, '<li>a</li><li>b</li><li>c</li>');
  });

  it('renders nothing for an empty array', () => {
    assert.equal(render('<li ace-each="x in list">{{ x }}</li>', { list: [] }), '');
  });

  it('renders nothing when the list key is missing', () => {
    assert.equal(render('<li ace-each="x in list">{{ x }}</li>', {}), '');
  });

  it('renders nothing when the list key is not an array', () => {
    assert.equal(render('<li ace-each="x in list">{{ x }}</li>', { list: 'not-array' }), '');
  });

  it('exposes loop variable for interpolation inside the element', () => {
    const result = render('<span ace-each="n in nums">{{ n }}</span>', { nums: [1, 2, 3] });
    assert.equal(result, '<span>1</span><span>2</span><span>3</span>');
  });
});

describe('render — combined directives', () => {
  it('ace-if and interpolation together', () => {
    assert.equal(
      render(
        '<div>' +
          '<p ace-if="show">{{ msg }}</p>' +
          '<p ace-if="!show">hidden</p>' +
          '</div>',
        { show: true, msg: 'visible' },
      ),
      '<div><p>visible</p></div>',
    );
  });

  it('nested ace-each with interpolation', () => {
    const result = render(
      '<ul><li ace-each="item in items">{{ item }}</li></ul>',
      { items: ['x', 'y'] },
    );
    assert.equal(result, '<ul><li>x</li><li>y</li></ul>');
  });
});
