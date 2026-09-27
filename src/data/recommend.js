import {items,suggestions} from './content.js';

/** Local, deterministic recommendations. Input text is never transmitted. */
export function recommend(message,language='en'){
  const key=String(message||'').trim().toLowerCase();
  if(!key)return [];
  let ids=suggestions[key];
  if(!ids){
    const suffix=Object.keys(suggestions).find(prefix=>key.endsWith(` ${prefix}`));
    if(suffix)ids=suggestions[suffix];
  }
  return (ids||[]).map(id=>items.find(item=>item.id===id)||items.find(item=>item.en.toLowerCase()===id.toLowerCase())).filter(Boolean).map(item=>({...item,label:item[language]||item.en}));
}
