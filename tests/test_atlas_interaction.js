/* Interaction test for the atlas.

 * Selecting a node threw ReferenceError on every kind of node, because
 * drawWeb called a helper that had never been written and select calls
 * drawWeb first. Hovering does not go through select, so the tooltip kept
 * working and the page looked alive while nothing could be clicked.
 *
 * The engine tests could not have caught this: the model was fine. This
 * boots the real application against a stub of three.js and clicks one node
 * of every kind in the payload.
 *
 * Run:  node tests/test_atlas_interaction.js
 */
const fs=require('fs');
const root=require('path').join(__dirname,'..');
const raw=fs.readFileSync(root+'/site/assets/atlas-data.js','utf8');
const D=JSON.parse(raw.slice(raw.indexOf('=')+1,raw.lastIndexOf(';')));
const THREE=require('./three-stub.js');

function El(id){
  return { id:id, textContent:'', innerHTML:'', value:'0', style:{},
    className:'', dataset:{}, children:[], offsetWidth:100, offsetHeight:40,
    clientWidth:900, clientHeight:600,
    appendChild(c){this.children.push(c);return c;},
    addEventListener(){}, removeEventListener(){}, setAttribute(){},
    getBoundingClientRect(){return {left:0,top:0,width:900,height:600};},
    classList:{add(){},remove(){},toggle(){},contains(){return false;}},
    querySelector(){return El('q');}, querySelectorAll(){return [];},
    getContext(){ return {
      createRadialGradient(){ return {addColorStop(){}}; },
      createLinearGradient(){ return {addColorStop(){}}; },
      fillRect(){}, clearRect(){}, beginPath(){}, arc(){}, fill(){}, stroke(){},
      moveTo(){}, lineTo(){}, closePath(){}, save(){}, restore(){},
      translate(){}, scale(){}, rotate(){}, drawImage(){}, fillText(){},
      measureText(){return {width:10};},
      getImageData(){return {data:new Uint8ClampedArray(4)};},
      putImageData(){}, set fillStyle(v){}, set strokeStyle(v){},
      set font(v){}, set globalAlpha(v){}, set lineWidth(v){} }; },
    focus(){}, blur(){}, width:256, height:256 };
}
const reg={};
global.document={
  getElementById(id){ return reg[id] || (reg[id]=El(id)); },
  createElement(t){ return El('new-'+t); },
  querySelector(){return El('q');}, querySelectorAll(){return [];},
  addEventListener(){}, body:El('body'),
  documentElement:El('html')
};
global.window={ ATLAS:D, THREE:THREE, addEventListener(){},
  innerWidth:1400, innerHeight:900, devicePixelRatio:1,
  getComputedStyle(){ return { getPropertyValue(){ return '#8b7ff2'; } }; },
  requestAnimationFrame(){ return 0; } };
global.requestAnimationFrame=()=>0;
global.getComputedStyle=global.window.getComputedStyle;
global.navigator={userAgent:'node'};

let bootError=null;
try { eval(fs.readFileSync(root+'/site/assets/atlas-app.js','utf8')); }
catch(e){ bootError=e; global.__stack=e.stack; }
if(bootError){ console.log('BOOT FAILED:', bootError.message);
  console.log(String(global.__stack).split('\n').slice(0,6).join('\n')); process.exit(1); }
const UI=global.window.__atlasUI;
if(!UI){ console.log('no UI handle — renderer did not initialise'); process.exit(1); }
console.log('booted. tabs =', UI.tabCount());
const BOOT_TAB = UI.openTab();

// click one node of every kind
const kinds={};
D.kind.forEach((k,i)=>{ const n=D.kinds[k]; if(kinds[n]===undefined) kinds[n]=i; });
let fails=0;
for(const [name,i] of Object.entries(kinds)){
  try {
    UI.select(i);
    const ok = UI.selected()===i;
    console.log(`  ${ok?'ok  ':'FAIL'} click a ${name.padEnd(11)} -> ${String(D.name[i]).slice(0,40)}`);
    if(!ok) fails++;
  } catch(e){
    fails++;
    console.log(`  FAIL click a ${name.padEnd(11)} threw: ${e.message}`);
  }
}
if(fails) process.exitCode = 2;

// the behaviour tab must offer both views, and both must be non-empty
try {
  const bt = UI.brainTab();
  UI.setTab(bt);
  const brainN = UI.layerSize();
  UI.setMindMap(true);
  const mapN = UI.layerSize();
  UI.setMindMap(false);
  const back = UI.layerSize();
  const ok = brainN > 0 && mapN > 0 && back === brainN;
  console.log(`  ${ok?'ok  ':'FAIL'} brain/map switcher: ${brainN} channels <-> ${mapN} districts`);
  if(!ok) process.exitCode = 2;
} catch(e){
  console.log('  FAIL brain/map switcher threw:', e.message);
  process.exitCode = 2;
}

// The opening tab must be the plant layer. It was the literal 4 in three
// separate places; inserting two tabs turned that into the markets layer.
// Sampled at boot, before any other check moves it.
{
  const id = D.tabs[BOOT_TAB] && D.tabs[BOOT_TAB].id;
  const ok = id === 'plants';
  console.log(`  ${ok?'ok  ':'FAIL'} opening tab is '${id}'`);
  if (!ok) process.exitCode = 2;
}

// selecting draws a web; clearing the selection must remove it
try {
  const station = D.kind.findIndex(k => D.kinds[k] === 'grid');
  UI.setTab(D.tabs.findIndex(t => t.id === 'grids'));
  UI.select(station);
  const drawn = UI.webSize();
  UI.clearSel();
  const after = UI.webSize();
  const ok = drawn > 0 && after === 0;
  console.log(`  ${ok?'ok  ':'FAIL'} web cleared with the selection: ${drawn} -> ${after}`);
  if (!ok) process.exitCode = 2;
} catch(e) { console.log('  FAIL web-clear check threw:', e.message); process.exitCode = 2; }

// every scenario must be reachable from the dropdown, and every one must move
// something: a prepared change that does nothing is worse than no entry
{
  const cats = D.scenarioCats || [];
  const filed = new Set();
  cats.forEach(c => Object.keys(D.scenarios)
    .filter(k => D.scenarios[k].cat === c.id).forEach(k => filed.add(k)));
  const all = Object.keys(D.scenarios);
  const orphan = all.filter(k => !filed.has(k));
  console.log(`  ${orphan.length===0?'ok  ':'FAIL'} all ${all.length} scenarios filed under ${cats.length} categories` +
              (orphan.length ? ` (orphans: ${orphan.slice(0,4)})` : ''));
  if (orphan.length) process.exitCode = 2;

  const missing = [];
  all.forEach(k => Object.keys(D.scenarios[k].shocks).forEach(id => {
    if (D.idMap[id] === undefined) missing.push(k + ':' + id);
  }));
  console.log(`  ${missing.length===0?'ok  ':'FAIL'} every shock targets a node that exists` +
              (missing.length ? ` (${missing.slice(0,3)})` : ''));
  if (missing.length) process.exitCode = 2;

  const inert = all.filter(k => (D.scenarios[k].reach || 0) <= 1);
  console.log(`  ${inert.length===0?'ok  ':'FAIL'} every scenario moves something` +
              (inert.length ? ` (inert: ${inert.slice(0,4)})` : ''));
  if (inert.length) process.exitCode = 2;

  const nolabel = all.filter(k => !D.scenarios[k].label || !D.scenarios[k].basis);
  console.log(`  ${nolabel.length===0?'ok  ':'FAIL'} every scenario has a label and a stated basis` +
              (nolabel.length ? ` (${nolabel.slice(0,3)})` : ''));
  if (nolabel.length) process.exitCode = 2;
}
