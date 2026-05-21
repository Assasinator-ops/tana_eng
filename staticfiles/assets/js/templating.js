export function tmpl(str, data={}){
  return str.replace(/\{\{(\w+)\}\}/g, (_,k)=> data[k] ?? '');
}
