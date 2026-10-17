(function () {
  'use strict';
  const buttons = Array.from(document.querySelectorAll('[data-view-target]'));
  const panels = Array.from(document.querySelectorAll('[data-view-panel]'));
  function selectView(name) {
    if (!buttons.some(function (button) { return button.dataset.viewTarget === name; })) return false;
    buttons.forEach(function (button) { button.setAttribute('aria-pressed', String(button.dataset.viewTarget === name)); });
    panels.forEach(function (panel) { panel.hidden = panel.dataset.viewPanel !== name; });
    return true;
  }
  function setFragment(ident) {
    if (window.location && window.location.hash !== '#' + ident) window.location.hash = ident;
  }
  function revealTarget(ident, focus) {
    const target = document.getElementById(ident);
    if (!target) return false;
    let parent = target;
    while (parent) {
      if (parent.dataset && parent.dataset.viewPanel) selectView(parent.dataset.viewPanel);
      if (parent.tagName === 'DETAILS') parent.open = true;
      parent = parent.parentElement;
    }
    if (focus) {
      target.scrollIntoView({block:'nearest',behavior:'auto'});
      const summary = target.querySelector('summary');
      if (summary) summary.focus({preventScroll:true});
    }
    return true;
  }
  function restoreFragment() {
    const ident = window.location ? window.location.hash.slice(1) : '';
    if (!ident && buttons.length) selectView(buttons[0].dataset.viewTarget);
    else if (ident.startsWith('view-')) selectView(ident.slice(5));
    else if (/^(org-|work-|workflow-)/.test(ident)) revealTarget(ident, true);
  }
  buttons.forEach(function (button, index) {
    button.addEventListener('click', function () { selectView(button.dataset.viewTarget); setFragment('view-' + button.dataset.viewTarget); });
    button.addEventListener('keydown', function (event) {
      let target = index;
      if (event.key === 'ArrowRight') target = (index + 1) % buttons.length;
      else if (event.key === 'ArrowLeft') target = (index + buttons.length - 1) % buttons.length;
      else if (event.key === 'Home') target = 0;
      else if (event.key === 'End') target = buttons.length - 1;
      else return;
      event.preventDefault();
      buttons[target].focus();
      selectView(buttons[target].dataset.viewTarget);
      setFragment('view-' + buttons[target].dataset.viewTarget);
    });
  });
  if (buttons.length) selectView(buttons[0].dataset.viewTarget);
  restoreFragment();
  window.addEventListener('hashchange', restoreFragment);
  document.querySelectorAll('a[href^="#org-"],a[href^="#work-"],a[href^="#workflow-"]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      const target = document.getElementById(link.getAttribute('href').slice(1));
      if (!target) return;
      event.preventDefault();
      revealTarget(target.id, true);
      setFragment(target.id);
    });
  });
  const chooser = document.getElementById('role-focus');
  const feedback = document.getElementById('role-focus-status');
  function locateRole() {
    const ident = chooser.value;
    const matches = [];
    document.querySelectorAll('[data-role-id]').forEach(function (node) {
      const match = Boolean(ident) && node.dataset.roleId === ident;
      node.classList.toggle('is-focused', match);
      if (match) matches.push(node);
    });
    const records = Array.from(document.querySelectorAll('[data-role-record]'));
    records.forEach(function (record) { if (ident && record.dataset.roleRecord === ident) record.open = true; });
    if (ident) {
      const register = document.querySelector('.role-register');
      if (register) register.open = true;
      const label = chooser.options[chooser.selectedIndex].text;
      feedback.textContent = label + ' is highlighted in ' + (matches.length === 2 ? 'both views.' : 'the view where it is recorded.') + ' Its recorded responsibilities are expanded below.';
      if (matches[0]) matches[0].scrollIntoView({ block: 'center', inline: 'center', behavior: 'auto' });
    } else {
      feedback.textContent = 'All recorded relationships remain visible.';
    }
  }
  if (chooser) {
    chooser.addEventListener('change', locateRole);
    document.getElementById('reset-role-focus').addEventListener('click', function () { chooser.value = ''; locateRole(); chooser.focus(); });
  }
  let printState = null;
  window.addEventListener('beforeprint', function () {
    if (printState) return;
    printState = Array.from(document.querySelectorAll('details')).map(function (detail) { return [detail, detail.open]; });
    printState.forEach(function (entry) { entry[0].open = true; });
  });
  window.addEventListener('afterprint', function () {
    if (!printState) return;
    printState.forEach(function (entry) { entry[0].open = entry[1]; });
    printState = null;
  });
}());
