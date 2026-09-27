import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

function worker(){
 const sourcePromise=readFile(new URL('../public/sw.js',import.meta.url),'utf8');
 return sourcePromise.then(source=>{
  const events={},stores=new Map();
  const keyOf=value=>typeof value==='string'?value:value.url;
  const cacheFactory=name=>{if(!stores.has(name))stores.set(name,new Map());const store=stores.get(name);return {put:async(key,value)=>store.set(keyOf(key),value.clone()),match:async key=>store.get(keyOf(key))?.clone(),addAll:async keys=>{for(const key of keys)store.set(key,new Response('cached'))}}};
  const self={location:{origin:'https://saathi.test'},addEventListener:(type,handler)=>events[type]=handler,skipWaiting:async()=>{},clients:{claim:async()=>{}}};
  let offline=false;
  const fetch=async input=>{if(offline)throw new Error('offline');const url=typeof input==='string'?input:input.url;const pathname=new URL(url,'https://saathi.test').pathname;if(pathname==='/')return new Response('<script type="module" src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">');return new Response(pathname.startsWith('/api/')?JSON.stringify([{id:'water'}]):'asset',{headers:{'Content-Type':pathname.startsWith('/api/')?'application/json':'text/plain'}})};
  const caches={open:async name=>cacheFactory(name),keys:async()=>[...stores.keys()],delete:async name=>stores.delete(name),match:async key=>{for(const store of stores.values()){const value=store.get(keyOf(key));if(value)return value.clone()}return undefined}};
  vm.runInNewContext(source,{self,caches,fetch,URL,Response,Promise,JSON});
  return {events,caches,setOffline:value=>{offline=value},fetch};
 });
}
test('service worker precaches app shell and falls back for reopened navigation offline',async()=>{
 const sw=await worker(),installEvent={waitUntil(promise){this.promise=promise}};sw.events.install(installEvent);await installEvent.promise;
 assert.ok(await sw.caches.match('/'));
 assert.ok(await sw.caches.match('/assets/app.js'));
 sw.setOffline(true);let navigation;sw.events.fetch({request:{method:'GET',url:'https://saathi.test/',mode:'navigate'},respondWith(promise){navigation=promise}});
 assert.ok(await navigation);
});
test('service worker caches essential catalog data for offline use',async()=>{
 const sw=await worker();const installEvent={waitUntil(promise){this.promise=promise}};sw.events.install(installEvent);await installEvent.promise;
 let onlineResponse;sw.events.fetch({request:{method:'GET',url:'https://saathi.test/api/categories',mode:'cors'},respondWith(promise){onlineResponse=promise}});assert.equal((await onlineResponse).status,200);
 sw.setOffline(true);let offlineResponse;sw.events.fetch({request:{method:'GET',url:'https://saathi.test/api/categories',mode:'cors'},respondWith(promise){offlineResponse=promise}});
 assert.equal((await offlineResponse).status,200);assert.match(await (await offlineResponse).text(),/water/);
});
