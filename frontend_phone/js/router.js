(function () {
  const FLOW_SCREENS = ['s-analyzing', 's-plans', 's-exec'];
  const TAB_SCREENS = ['s-home', 's-map', 's-trips', 's-profile'];
  const enterCallbacks = new Map();
  const leaveCallbacks = new Map();
  let currentScreen = 's-home';

  function runCallbacks(map, id) {
    (map.get(id) || []).forEach(callback => {
      try { callback(id); } catch (error) { console.error(error); }
    });
  }

  function goTo(id) {
    if (!document.getElementById(id)) return;
    if (currentScreen && currentScreen !== id) runCallbacks(leaveCallbacks, currentScreen);
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(id);
    target.classList.remove('active');
    void target.offsetWidth;
    target.classList.add('active');
    const scrollBody = target.querySelector('.scroll-body');
    if (scrollBody) scrollBody.scrollTop = 0;
    currentScreen = id;
    runCallbacks(enterCallbacks, id);
  }

  function switchTab(id) {
    goTo(id);
    document.querySelectorAll('.bnav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.bnav-item').forEach(el => {
      const onclick = el.getAttribute('onclick') || '';
      if (onclick.includes(`'${id}'`) || onclick.includes(`\"${id}\"`)) {
        el.classList.add('active');
      }
    });
  }

  function onEnter(screenId, callback) {
    if (!enterCallbacks.has(screenId)) enterCallbacks.set(screenId, []);
    enterCallbacks.get(screenId).push(callback);
  }

  function onLeave(screenId, callback) {
    if (!leaveCallbacks.has(screenId)) leaveCallbacks.set(screenId, []);
    leaveCallbacks.get(screenId).push(callback);
  }

  Object.assign(window, {
    FLOW_SCREENS,
    TAB_SCREENS,
    goTo,
    switchTab,
    onEnter,
    onLeave
  });
})();
