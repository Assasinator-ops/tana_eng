/* Tiny jQuery-like shim for selection & events (NOT a full jQuery replacement) */
window.$ = (sel, ctx=document)=>ctx.querySelector(sel);
window.$$.all = (sel, ctx=document)=>Array.from(ctx.querySelectorAll(sel));
Element.prototype.on = function(evt, cb){ this.addEventListener(evt, cb); return this; };
