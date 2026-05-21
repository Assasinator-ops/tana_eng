export function setupDropzone(el, {onFiles}={}){
  el.addEventListener('dragover', (e)=>{e.preventDefault(); el.classList.add('ring')});
  el.addEventListener('dragleave', ()=>el.classList.remove('ring'));
  el.addEventListener('drop', (e)=>{ e.preventDefault(); el.classList.remove('ring'); onFiles && onFiles([...e.dataTransfer.files]); });
}
