export const Dom = {
  html:(el, html)=>{ el.innerHTML=html; return el; },
  el:(tag, attrs={})=> Object.assign(document.createElement(tag), attrs),
  qs:(s,sc=document)=>sc.querySelector(s),
  qsa:(s,sc=document)=>Array.from(sc.querySelectorAll(s))
};
