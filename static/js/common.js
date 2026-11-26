// Apply the saved theme as soon as this file loads to reduce theme flashing.
(function(){
  let saved="dark";
  try{saved=localStorage.getItem("mcp-canarytrap-theme")||"dark";}catch(_){}
  document.documentElement.dataset.theme=saved==="light"?"light":"dark";
})();

document.addEventListener("DOMContentLoaded",()=>{
  const mount=document.getElementById("app-nav");
  if(!mount)return;
  const links=[
    ["/dashboard","Overview"],
    ["/cve","CVE case study"],
    ["/simulation","Simulation"],
    ["/auditor","Auditor"],
    ["/url-validator","URL validator"],
    ["/decoy-monitor","Decoy monitor"]
  ];
  const current=window.location.pathname;
  const nav=links.map(([href,label])=>{
    const active=current===href;
    return `<a href="${href}"${active?' class="active" aria-current="page"':''}>${label}</a>`;
  }).join("");
  const theme=document.documentElement.dataset.theme||"dark";
  mount.innerHTML=`
    <header class="site-header">
      <a class="brand" href="/dashboard" aria-label="MCP-CanaryTrap home">MCP-CanaryTrap</a>
      <nav aria-label="Main navigation">${nav}</nav>
      <div class="header-actions">
        <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Switch to ${theme==="dark"?"light":"dark"} theme" title="Switch theme">
          <span class="theme-icon" aria-hidden="true">${theme==="dark"?"☀":"☾"}</span>
          <span class="theme-label">${theme==="dark"?"Light mode":"Dark mode"}</span>
        </button>
        <form method="post" action="/auth/logout">
          <button class="secondary" type="submit">Log out</button>
        </form>
      </div>
    </header>`;
  const toggle=document.getElementById("theme-toggle");
  toggle?.addEventListener("click",()=>{
    const next=document.documentElement.dataset.theme==="dark"?"light":"dark";
    document.documentElement.dataset.theme=next;
    try{localStorage.setItem("mcp-canarytrap-theme",next);}catch(_){}
    const light=next==="light";
    toggle.innerHTML=`<span class="theme-icon" aria-hidden="true">${light?"☾":"☀"}</span><span class="theme-label">${light?"Dark mode":"Light mode"}</span>`;
    toggle.setAttribute("aria-label",`Switch to ${light?"dark":"light"} theme`);
  });
});

async function api(path,body){
  const response=await fetch(path,{
    method:body?"POST":"GET",
    headers:body?{"Content-Type":"application/json"}:{},
    body:body?JSON.stringify(body):undefined
  });
  const data=await response.json().catch(()=>({detail:response.statusText}));
  if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail||data));
  return data;
}
function show(id,value){
  const element=document.getElementById(id);
  if(element)element.textContent=JSON.stringify(value,null,2);
}
