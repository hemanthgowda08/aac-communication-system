const timeoutMs=1800;
export async function api(path,{method='GET',body,signal}={}){
 const timeout=typeof AbortSignal!=='undefined'&&typeof AbortSignal.timeout==='function'?AbortSignal.timeout(timeoutMs):undefined;
 const response=await fetch(`/api${path}`,{method,headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined,signal:signal||timeout});
 const data=await response.json().catch(()=>({error:'The server returned an unreadable response.'}));
 if(!response.ok)throw new Error(data.error||`Request failed (${response.status}).`);
 return data;
}
export const toPhrase=(phrase)=>({...phrase,translations:typeof phrase.translations==='string'?JSON.parse(phrase.translations):phrase.translations||{}});
