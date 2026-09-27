const APP_CACHE='saathi-app-v1';
const DATA_CACHE='saathi-data-v1';
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const cache=await caches.open(APP_CACHE);
 const response=await fetch('/');
 await cache.put('/',response.clone());
 const html=await response.text();
 const assets=[...html.matchAll(/(?:src|href)="([^"]+\.(?:js|css)(?:\?[^"]*)?)"/g)].map(match=>match[1]);
 await Promise.allSettled(assets.map(async asset=>{const item=await fetch(asset);if(item.ok)await cache.put(asset,item)}));
 await cache.addAll(['/manifest.webmanifest','/icons/saathi.svg']);
 const dataCache=await caches.open(DATA_CACHE);
 await Promise.allSettled(['/api/categories','/api/items'].map(async path=>{const data=await fetch(path);if(data.ok)dataCache.put(path,data.clone())}));
 self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 const keys=await caches.keys();await Promise.all(keys.filter(key=>key.startsWith('saathi-')&&![APP_CACHE,DATA_CACHE].includes(key)).map(key=>caches.delete(key)));
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 const request=event.request;
 if(request.method!=='GET'||new URL(request.url).origin!==self.location.origin)return;
 const url=new URL(request.url);
 if(url.pathname==='/api/categories'||url.pathname==='/api/items'){
  event.respondWith((async()=>{const cache=await caches.open(DATA_CACHE),cached=await cache.match(request);try{const fresh=await fetch(request);if(fresh.ok)cache.put(request,fresh.clone());return fresh}catch{return cached||new Response(JSON.stringify({error:'Offline and no cached copy is available.'}),{status:503,headers:{'Content-Type':'application/json'}})}})());return;
 }
 if(url.pathname.startsWith('/api/'))return;
 if(request.mode==='navigate'){
  event.respondWith((async()=>{try{const response=await fetch(request);const cache=await caches.open(APP_CACHE);cache.put('/',response.clone());return response}catch{return await caches.match('/')||Response.error()}})());return;
 }
 if(url.pathname.startsWith('/assets/')||url.pathname==='/manifest.webmanifest'||url.pathname==='/icons/saathi.svg'){
  event.respondWith((async()=>{const cache=await caches.open(APP_CACHE),cached=await cache.match(request);if(cached)return cached;const response=await fetch(request);if(response.ok)cache.put(request,response.clone());return response})());
 }
});
