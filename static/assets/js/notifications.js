import {bus} from './pubsub.js';

const state={queue:[], listeners:[], channel:'default'};

export const Notifications = {
  async requestPermission(){
    if(!('Notification' in window)) return 'unsupported';
    if(Notification.permission==='granted') return 'granted';
    if(Notification.permission!=='denied') return await Notification.requestPermission();
    return 'denied';
  },
  setChannel(name){ state.channel=name; },
  on(fn){ state.listeners.push(fn); return ()=>{ state.listeners=state.listeners.filter(x=>x!==fn); }; },
  push(msg, opts={}){
    const note = { id:crypto.randomUUID ? crypto.randomUUID() : String(Date.now()+Math.random()), msg, ts:Date.now(), channel: state.channel, ...opts };
    state.queue.push(note);
    state.listeners.forEach(fn=>fn(note));
    bus.emit('notify', note);
    if(opts.native && 'Notification' in window && Notification.permission==='granted'){
      new Notification(opts.title||'Notification', { body: msg, icon: opts.icon });
    }
    return note.id;
  },
  schedule(msg, when, opts={}){
    const delay = Math.max(0, when - Date.now());
    return setTimeout(()=>Notifications.push(msg, opts), delay);
  },
  clear(){ state.queue.length=0; },
  getQueue(){ return [...state.queue]; }
};
// UI helper to render toasts into a container
export function mountToastHost(){
  let host=document.querySelector('.toast-host');
  if(!host){ host=document.createElement('div'); host.className='toast-host'; Object.assign(host.style,{position:'fixed',right:'1rem',top:'1rem',display:'grid',gap:'.5rem',zIndex:'60'}); document.body.appendChild(host); }
  Notifications.on(n=>{
    const el=document.createElement('div');
    el.className='toast card';
    el.innerHTML = `<div class="flex items-center gap-2"><svg width="16" height="16"><use href="./assets/icons.svg#icon-bell"/></svg><strong>${n.title||'Notice'}</strong></div><div class="text-sm text-gray-700">${n.msg}</div>`;
    host.appendChild(el);
    setTimeout(()=>{ el.style.opacity='.9'; }, 20);
    setTimeout(()=>{ el.remove(); }, n.ttl||4000);
  });
}
