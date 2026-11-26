async function refresh(){const s=await (await fetch('/api/evidence')).json();document.getElementById('record-count').textContent=s.records;await verify()}
async function verify(){const r=await fetch('/api/evidence/verify');const v=await r.json();document.getElementById('chain-status').textContent=v.valid?'VALID':'BROKEN';document.getElementById('chain-status').className=v.valid?'good':'danger';document.getElementById('verify-result').textContent=JSON.stringify(v,null,2)}
document.getElementById('verify').addEventListener('click',verify);refresh();
