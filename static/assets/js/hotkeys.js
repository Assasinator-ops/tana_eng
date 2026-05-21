export function hotkey(combo, handler){
  const keys = combo.toLowerCase().split('+').map(s=>s.trim());
  function match(e){
    const set = new Set(keys);
    if(set.has('ctrl')&&!e.ctrlKey) return false;
    if(set.has('shift')&&!e.shiftKey) return false;
    if(set.has('alt')&&!e.altKey) return false;
    const key = keys[keys.length-1];
    return e.key.toLowerCase()===key;
  }
  function onKey(e){ if(match(e)){ e.preventDefault(); handler(e); } }
  window.addEventListener('keydown', onKey);
  return ()=>window.removeEventListener('keydown', onKey);
}
