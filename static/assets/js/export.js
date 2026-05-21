export function exportTableToCSV(table, filename='table.csv'){
  const rows = [...table.querySelectorAll('tr')];
  const csv = rows.map(r => [...r.cells].map(c => `"${c.textContent.replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
export function exportJSON(data, filename='data.json'){
  const blob = new Blob([JSON.stringify(data, null, 2)],{type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
