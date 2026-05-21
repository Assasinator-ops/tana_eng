export class PubSub{
  constructor(){this.events=new Map();}
  on(evt,fn){(this.events.get(evt)||this.events.set(evt,[]).get(evt)).push(fn); return ()=>this.off(evt,fn);}
  off(evt,fn){const a=this.events.get(evt)||[]; const i=a.indexOf(fn); if(i>-1)a.splice(i,1);}
  emit(evt,data){(this.events.get(evt)||[]).forEach(fn=>{try{fn(data)}catch(e){console.error(e)}});}
}
export const bus = new PubSub();
