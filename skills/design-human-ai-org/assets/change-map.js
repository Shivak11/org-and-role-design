(() => {
  'use strict';
  const controls = document.querySelector('.view-controls');
  const buttons = [...document.querySelectorAll('[data-view-target]')];
  const panels = [...document.querySelectorAll('[data-view-panel]')];
  if (!controls || !buttons.length || !panels.length) return;
  function selectView(view, focus = false) {
    if (!panels.some(panel => panel.dataset.viewPanel === view)) return;
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.viewTarget === view)));
    panels.forEach(panel => { panel.hidden = panel.dataset.viewPanel !== view; });
    if (focus) buttons.find(button => button.dataset.viewTarget === view)?.focus();
  }
  document.documentElement.classList.add('js-ready');
  controls.hidden = false;
  selectView('release');
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => selectView(button.dataset.viewTarget));
    button.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
      else if (event.key === 'ArrowLeft') next = (index - 1 + buttons.length) % buttons.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = buttons.length - 1;
      else return;
      event.preventDefault();
      selectView(buttons[next].dataset.viewTarget, true);
    });
  });
  const printState = new Map();
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('details').forEach(details => {
      printState.set(details, details.open);
      details.open = true;
    });
  });
  window.addEventListener('afterprint', () => {
    printState.forEach((open, details) => { details.open = open; });
    printState.clear();
  });
})();
