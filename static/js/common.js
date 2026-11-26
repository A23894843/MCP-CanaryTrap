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
  mount.innerHTML=`
    <header class="site-header">
      <a class="brand" href="/dashboard" aria-label="MCP-CanaryTrap home">MCP-CanaryTrap</a>
      <nav aria-label="Main navigation">${nav}</nav>
      <form method="post" action="/auth/logout">
        <button class="secondary" type="submit">Log out</button>
      </form>
    </header>`;
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
