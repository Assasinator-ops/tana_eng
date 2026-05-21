export function simpleLineChart(canvas, data){
  const ctx = canvas.getContext('2d');
  const w = canvas.width = canvas.clientWidth;
  const h = canvas.height = canvas.clientHeight;
  ctx.clearRect(0,0,w,h);
  const xs = data.map((_,i)=> i/(data.length-1)*(w-20)+10);
  const min=Math.min(...data), max=Math.max(...data);
  const ys = data.map(v => h-10 - (v-min)/(max-min||1)*(h-20));
  ctx.beginPath(); ctx.moveTo(xs[0], ys[0]);
  for(let i=1;i<xs.length;i++){ ctx.lineTo(xs[i], ys[i]); }
  ctx.stroke();
}
