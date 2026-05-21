import {bus} from './pubsub.js';
export function createStore(initial={}){
  const state = structuredClone ? structuredClone(initial) : JSON.parse(JSON.stringify(initial));
  return {
    get: (k)=> state[k],
    set: (k,v)=>{ state[k]=v; bus.emit('store:'+k,v); },
    all: ()=> ({...state})
  };
}
