async function refreshEvents(){
  try{
    const [events,decoys]=await Promise.all([api("/api/events"),api("/api/decoys")]);
    const body=document.getElementById("events-body");
    if(body)body.innerHTML=events.map(e=>`<tr><td>${e.id}</td><td>${esc(e.target_name)}</td><td>${esc(e.event_type)}</td><td>${esc(e.severity)}</td><td>${esc(e.source)}</td><td>${esc(e.timestamp)}</td></tr>`).join("")||'<tr><td colspan="6">No events yet</td></tr>';
    const list=document.getElementById("decoy-list");
    if(list){
      list.innerHTML=decoys.map(d=>`
        <article class="decoy">
          <div class="heading"><span class="tag">${esc(d.category||"Decoy")}</span><span class="tag ${esc(d.severity)}">${esc(d.severity)}</span></div>
          <h3><code>${esc(d.name)}</code></h3>
          <p>${esc(d.description)}</p>
          <button type="button" class="inspect-decoy" data-tool="${esc(d.name)}">Inspect tool</button>
        </article>`).join("");
      list.querySelectorAll(".inspect-decoy").forEach(button=>{
        button.addEventListener("click",()=>inspectTool(button.dataset.tool));
      });
    }
    const options=document.getElementById("tool-options");
    if(options)options.innerHTML=decoys.map(d=>`<option value="${esc(d.name)}">`).join("")+'<option value="weather_search">';
    const count=document.getElementById("decoy-count");
    if(count)count.textContent=String(decoys.length);
  }catch(e){console.error(e)}
}
function esc(s){
  return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
async function inspectTool(name){
  try{
    const result=await api("/api/suite/inspect-tool",{tool_name:name});
    show("tool-output",result);
    const input=document.getElementById("tool-name");
    if(input)input.value=name;
    await refreshEvents();
  }catch(e){show("tool-output",{error:e.message})}
}
document.getElementById("inspect-button").onclick=()=>inspectTool(document.getElementById("tool-name").value);
document.getElementById("refresh-button").onclick=refreshEvents;
refreshEvents();
setInterval(refreshEvents,5000);
