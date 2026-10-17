(() => {
  'use strict';
  const diagram = document.querySelector('.diagram');
  const viewport = document.querySelector('.diagram-scroll');
  const sizer = document.querySelector('.diagram-sizer');
  if (!diagram || !viewport || !sizer) return;
  document.documentElement.classList.add('js-ready');
  const width = Number(diagram.dataset.width);
  const height = Number(diagram.dataset.height);
  const controls = document.querySelector('.zoom-controls');
  controls.hidden = false;
  let scale = 1;
  let fitMode = true;
  const applyScale = (next) => {
    scale = Math.max(0.5, Math.min(1.5, next));
    diagram.style.transform = `scale(${scale})`;
    sizer.style.width = `${width * scale}px`;
    sizer.style.height = `${height * scale}px`;
    document.querySelector('#zoom-label').textContent = `${Math.round(scale * 100)}%`;
  };
  const fit = () => {
    const available = viewport.clientWidth - 2;
    // Keep the chart readable on a narrow phone and allow diagram-only scrolling.
    applyScale(available < 600 ? 0.9 : Math.max(0.8, Math.min(1, available / width)));
  };
  controls.addEventListener('click', (event) => {
    const button = event.target.closest('[data-zoom]');
    if (!button) return;
    const action = button.dataset.zoom;
    fitMode = action === 'fit';
    if (fitMode) fit();
    else applyScale(scale + (action === 'in' ? 0.1 : -0.1));
  });
  document.querySelectorAll('[data-select]').forEach(button => {
    button.addEventListener('click', () => {
      const index = button.dataset.select;
      document.querySelectorAll('[data-panel]').forEach(panel => {
        panel.classList.toggle('is-selected', panel.dataset.panel === index);
      });
      document.querySelectorAll('[data-select]').forEach(node => {
        node.setAttribute('aria-expanded', String(node.dataset.select === index));
      });
      const heading = document.querySelector(`#person-heading-${index}`);
      if (heading) {
        heading.focus({preventScroll: true});
        heading.scrollIntoView({block: 'start', behavior: 'instant'});
      }
    });
  });
  const reflow = () => { if (fitMode) fit(); };
  if ('ResizeObserver' in window) new ResizeObserver(reflow).observe(viewport);
  else window.addEventListener('resize', reflow);
  const openStates = new Map();
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('details').forEach(details => {
      openStates.set(details, details.open);
      details.open = true;
    });
  });
  window.addEventListener('afterprint', () => {
    openStates.forEach((state, details) => { details.open = state; });
    openStates.clear();
  });
  fit();
})();
