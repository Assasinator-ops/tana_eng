// Simple DataTable-like utility (vanilla JS)
export function SimpleTable(table, {pageSize=10}={}){
  const state = { page:0, pageSize, rows:[...table.tBodies[0].rows], filter:'' };
  const tbody = table.tBodies[0];
  function apply(){
    let rows = state.rows;
    if(state.filter){
      rows = rows.filter(r => r.textContent.toLowerCase().includes(state.filter.toLowerCase()));
    }
    rows.forEach(r=>r.style.display='none');
    const start = state.page*state.pageSize;
    rows.slice(start, start+state.pageSize).forEach(r=>r.style.display='');
  }
  function sortBy(idx, asc=true){
    state.rows.sort((a,b)=>{
      const A=a.cells[idx].textContent.trim();
      const B=b.cells[idx].textContent.trim();
      const nA=parseFloat(A), nB=parseFloat(B);
      if(!isNaN(nA)&&!isNaN(nB)) return asc? nA-nB : nB-nA;
      return asc? A.localeCompare(B) : B.localeCompare(A);
    });
    apply();
  }
  function filter(q){ state.filter=q||''; state.page=0; apply(); }
  function next(){ state.page++; apply(); }
  function prev(){ state.page=Math.max(0, state.page-1); apply(); }
  apply();
  return {sortBy, filter, next, prev, state};
}
