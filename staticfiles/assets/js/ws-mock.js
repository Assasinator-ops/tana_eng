import {bus} from './pubsub.js';
export function startMockSocket(){
  setInterval(()=>{
    const evt={type:'ping', ts:Date.now(), value: Math.random()};
    bus.emit('ws', evt);
  }, 3000);
}
