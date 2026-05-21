export const storage={
  get:(k,def=null)=>{try{return JSON.parse(localStorage.getItem(k)) ?? def}catch{return def}},
  set:(k,v)=>localStorage.setItem(k,JSON.stringify(v)),
  del:(k)=>localStorage.removeItem(k)
};
