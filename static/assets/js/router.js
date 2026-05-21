import {bus} from './pubsub.js';
export function createRouter(routes){
  function match(){ const path=location.hash.replace(/^#/, '')||'/'; const r=routes[path]||routes['*']; bus.emit('route', {path, component:r}); r && r(); }
  window.addEventListener('hashchange', match);
  document.addEventListener('DOMContentLoaded', match);
  return {navigate:(p)=>{location.hash=p;}};
}
