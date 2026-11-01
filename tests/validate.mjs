/**
 * BitcoinVersus.Tech U.S. Data Center Power Atlas — source and personal-map tests.
 * Run: node tests/validate.mjs
 * No npm dependencies required.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const chunks=Array.from({length:7},(_,i)=>i===6?'data/states-07-national.json':'data/states-0'+(i+1)+'.json');
const groups=chunks.map(p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8')));
const all=groups.flat();
const state=all.filter(p=>p.rank!==null),national=all.filter(p=>p.nationalRank!==null);
assert.equal(new Set(state.map(p=>p.state)).size,50,'50 state articles must be represented');
assert.equal(national.length,10,'national Top 10 must have exactly ten entries');
assert.equal(state.length,156,'state rankings: 48×3 + Texas×7 + Virginia×5');
assert.equal(all.length,166,'166 total ranking records');
assert.equal(new Set(all.map(p=>p.id)).size,all.length,'record IDs must be unique');
for(const p of all){
  assert(p.name&&p.heading&&p.brief&&p.article,'Each ranked record needs a name, headline, brief, and source article');
  assert(/^https:\/\/bitcoinversus\.tech\//.test(p.article),'Article must point to BitcoinVersus.Tech');
  assert(p.capacityMW===null||(Number.isFinite(p.capacityMW)&&p.capacityMW>=0),'Capacity must be a nonnegative MW quantity or null');
  assert(p.capacityLabel,'Figures without disclosed capacity must be identified as missing');
}
for(const st of new Set(state.map(p=>p.state))){
  const ranks=state.filter(p=>p.state===st).map(p=>p.rank).sort((a,b)=>a-b);
  const target=st==='Texas'?7:st==='Virginia'?5:3;
  assert.deepEqual(ranks,Array.from({length:target},(_,i)=>i+1),'Ranks must be complete in '+st);
}
assert.deepEqual(national.map(p=>p.nationalRank).sort((a,b)=>a-b),[1,2,3,4,5,6,7,8,9,10]);
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const inline=html.match(/<script>([\s\S]*?)<\/script>/);
assert(inline,'The interactive page must have its controller script');
new vm.Script(inline[1],{filename:'energy-map/index.html'});
for(const id of ['addSite','exportMap','importMap','mapFile','refreshAtlas','detail','map']){
  assert(html.includes('id="'+id+'"'),'Expected control '+id);
}
// Test personal site validation and storage round-trip without a browser runtime.
const noBoot=inline[1].replace(/\bboot\(\);\s*$/,'');
const mem=new Map();
const localStorage={setItem:(k,v)=>mem.set(k,String(v)),getItem:k=>mem.get(k)||null};
const fn=new Function('localStorage',noBoot+';return {normalizeImport,validPersonal,loadPersonal,savePersonal,stage,location,sanitizeUrl,setPersonal:p=>{personal=p}};');
const a=fn(localStorage);
const site=a.normalizeImport({name:'My wind farm',lat:41.5,lon:-92.5,state:'Iowa',capacityMW:120,productionMW:46,
  customStatus:'operating',capacityBasis:'Installed generation capacity',energyType:'Wind',energyMWh:52000,energyPeriod:'calendar year 2026',article:'https://example.org/plant'});
assert(a.validPersonal(site),'User-supplied point must validate');
assert.equal(a.stage(site),'operating','Personal status remains explicit');
assert.equal(a.location(site).lat,41.5,'Personal coordinates must be used unchanged');
assert.equal(a.sanitizeUrl('javascript:alert(1)'),'','Script schemes must be rejected');
assert.equal(a.normalizeImport({name:'invalid',lat:1234,lon:-90}),null,'Out of range coordinates rejected');
a.setPersonal([site]);
assert(a.savePersonal(),'Custom records must persist');
assert.equal(a.loadPersonal()[0].name,'My wind farm','Custom records must survive reload');
assert.equal(a.loadPersonal()[0].energyMWh,52000,'Period-qualified MWh data must survive reload');
console.log('PASS: 166 records; 50 states; 10 national; UI script; personal map validation and persistence.');
