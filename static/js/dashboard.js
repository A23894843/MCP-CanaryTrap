const el = id => document.getElementById(id);
async function api(url, options={}) {
  const r = await fetch(url, options);
  if (!r.ok) {
    const d = await r.json().catch(()=>({}));
    throw new Error(typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail || d));
  }
  return r.json();
}
const post = (url, body) => api(url, {
  method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)
});
function show(id, value) { el(id).textContent = JSON.stringify(value, null, 2); }

async function refresh() {
  try {
    const [s, events, decoys, status] = await Promise.all([
      api("/api/stats"), api("/api/events?limit=100"), api("/api/decoys"), api("/api/suite/status")
    ]);
    el("api-status").textContent = "All modules online";
    el("total-events").textContent=s.total_events;
    el("decoy-events").textContent=s.decoy_detections;
    el("critical-events").textContent=s.critical_events;
    el("high-events").textContent=s.high_events;
    const cards=el("decoy-list"); cards.replaceChildren();
    decoys.forEach(d=>{
      const c=document.createElement("div"); c.className="decoy";
      const n=document.createElement("strong"); n.textContent=d.name;
      const p=document.createElement("p"); p.textContent=d.description;
      const tag=document.createElement("span"); tag.className=`tag ${d.severity}`; tag.textContent=d.severity;
      c.append(n,p,tag); cards.append(c);
    });
    const body=el("events-body"); body.replaceChildren();
    if(!events.length) {
      const tr=document.createElement("tr"), td=document.createElement("td");
      td.colSpan=6; td.textContent="No events recorded yet."; tr.append(td); body.append(tr);
    } else events.forEach(e=>{
      const tr=document.createElement("tr");
      [e.id,e.target_name,e.event_type,e.severity,e.source,e.timestamp].forEach(v=>{
        const td=document.createElement("td"); td.textContent=String(v??"");
        if(v===e.severity){const tag=document.createElement("span");tag.className=`tag ${v}`;tag.textContent=v;td.replaceChildren(tag);}
        tr.append(td);
      }); body.append(tr);
    });
  } catch(err) { el("api-status").textContent=`API error: ${err.message}`; }
}

el("simulate-button").addEventListener("click", async()=>{
  try {
    show("simulation-output", await post("/api/suite/simulate", {
      authorization_endpoint:el("sim-endpoint").value
    }));
  } catch(e) { el("simulation-output").textContent=e.message; }
});
el("audit-button").addEventListener("click", async()=>{
  try {
    show("audit-output", await post("/api/suite/audit", {paths:[el("audit-path").value]}));
  } catch(e) { el("audit-output").textContent=e.message; }
});
el("validate-button").addEventListener("click", async()=>{
  try {
    show("url-output", await post("/api/suite/validate-url", {
      authorization_endpoint:el("url-endpoint").value
    }));
  } catch(e) { el("url-output").textContent=e.message; }
});
el("inspect-button").addEventListener("click", async()=>{
  try {
    show("tool-output", await post("/api/suite/inspect-tool", {tool_name:el("tool-name").value}));
    await refresh();
  } catch(e) { el("tool-output").textContent=e.message; }
});
el("refresh-button").addEventListener("click",refresh);
refresh();
setInterval(refresh,5000);
