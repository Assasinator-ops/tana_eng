export const Validator = {
  required:(v)=> !!(v||'').toString().trim() || 'Required',
  email:(v)=>/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email',
  min:(n)=>(v)=> (v||'').length>=n || `Min ${n} chars`,
  max:(n)=>(v)=> (v||'').length<=n || `Max ${n} chars`,
  number:(v)=>!isNaN(parseFloat(v)) || 'Not a number',
};
