export function createI18n(dict, lang='en'){
  let current=lang;
  function t(key, vars={}){
    const raw=(dict[current]&&dict[current][key])||(dict['en']&&dict['en'][key])||key;
    return raw.replace(/\{(\w+)\}/g, (_,k)=>vars[k]??'');
  }
  return { t, setLang:(l)=>current=l, getLang:()=>current };
}
