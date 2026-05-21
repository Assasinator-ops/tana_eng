export function serializeForm(form){
  const d=new FormData(form); const obj={};
  for(const [k,v] of d.entries()){ if(obj[k]){ if(Array.isArray(obj[k])) obj[k].push(v); else obj[k]=[obj[k],v]; } else obj[k]=v; }
  return obj;
}
