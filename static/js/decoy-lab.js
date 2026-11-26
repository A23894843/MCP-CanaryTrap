async function loadDecoys(){const r=await fetch('/decoys');const data=await r.json();const box=document.getElementById('decoy-list');box.replaceChildren();data.forEach(d=>{const el=document.createElement('article');el.className='card';const h=document.createElement('h3');h.textContent=d.name;const p=document.createElement('p');p.textContent=d.description+' • '+d.type;el.append(h,p);box.append(el)})}
async function inspect(value){const r=await fetch('/inspect?target_name='+encodeURIComponent(value),{method:'POST'});const data=await r.json();document.getElementById('result').textContent=JSON.stringify(data,null,2)}
document.getElementById('inspect').addEventListener('click',()=>inspect(document.getElementById('target').value.trim()));
document.getElementById('normal').addEventListener('click',()=>{document.getElementById('target').value='weather_search';inspect('weather_search')});
loadDecoys();
