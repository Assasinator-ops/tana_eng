// App helpers: dark mode, modal, toast, confirm dialogs (vanilla JS)
(function(){
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const root = document.documentElement;
  if(localStorage.getItem('theme')==='dark' || (!localStorage.getItem('theme') && prefersDark)){
    root.classList.add('dark');
  }
  document.addEventListener('click', (e)=>{
    const t = e.target.closest('[data-toggle-theme]');
    if(t){ root.classList.toggle('dark'); localStorage.setItem('theme', root.classList.contains('dark')?'dark':'light'); }
    const open = e.target.closest('[data-modal-open]');
    if(open){ document.querySelector(open.dataset.modalOpen)?.classList.add('open'); }
    const close = e.target.closest('[data-modal-close]');
    if(close){ document.querySelector(close.dataset.modalClose)?.classList.remove('open'); }
  });
  window.toast = (msg)=>{
    const el = document.createElement('div');
    el.className='toast';
    el.textContent=msg;
    document.body.appendChild(el);
    setTimeout(()=>el.remove(), 3000);
  };
  window.confirmDialog = async(message)=>{
    return new Promise(res=>{
      const host = document.createElement('div');
      host.className = 'modal open';
      host.innerHTML = '<div class="modal-dialog"><div style="padding:1rem">'+message+'</div><div style="display:flex;gap:.5rem;justify-content:flex-end;padding:1rem"><button class="btn btn-outline" data-no>No</button><button class="btn btn-primary" data-yes>Yes</button></div></div>';
      document.body.appendChild(host);
      host.querySelector('[data-yes]').onclick=()=>{ host.remove(); res(true); };
      host.querySelector('[data-no]').onclick=()=>{ host.remove(); res(false); };
    });
  };
})();
