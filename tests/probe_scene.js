/* What is actually in the scene, with nothing selected. */
const fs=require('fs'), path=require('path');
const root=path.join(__dirname,'..');
const t=fs.readFileSync(path.join(__dirname,'test_atlas_interaction.js'),'utf8');
eval(t.slice(0, t.indexOf('let bootError')));
let err=null;
try{ eval(fs.readFileSync(root+'/site/assets/atlas-app.js','utf8')); }catch(e){ err=e; }
if(err){ console.log('boot failed:', err.message); process.exit(1); }
const S=global.window.__atlasScene();
const g=S.globe.filter(o=>o.verts>0);
console.log('globe children carrying geometry:', g.length);
g.forEach((o,i)=>console.log('   #'+i,'verts='+o.verts,'visible='+o.visible));
console.log('web vertices with nothing selected:', S.web);
