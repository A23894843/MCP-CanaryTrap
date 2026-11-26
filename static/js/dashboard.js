async function loadDashboard(){
  try{
    const [eventsRes,decoysRes,healthRes]=await Promise.all([fetch('/events'),fetch('/decoys'),fetch('/health')]);
    const events=await eventsRes.json(),decoys=await decoysRes.json(),health=await healthRes.json();
    document.getElementById('total-events').textContent=events.length;
    document.getElementById('detections').textContent=events.filter(e=>e[2]==='DECOY_ACCESS').length;
    document.getElementById('decoy-count').textContent=decoys.length;
    document.getElementById('api-status').textContent=health.status==='ok'?'Online':'Unavailable';
    const body=document.getElementById('event-table');body.replaceChildren();
    if(!events.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=5;td.textContent='No events recorded yet. Try a decoy in the Decoy Lab.';tr.append(td);body.append(tr);}
    events.forEach(e=>{const tr=document.createElement('tr');e.forEach(v=>{const td=document.createElement('td');td.textContent=v??'';tr.append(td)});body.append(tr)});
  }catch(err){document.getElementById('api-status').textContent='Offline';console.error(err)}
}
loadDashboard();setInterval(loadDashboard,5000);
