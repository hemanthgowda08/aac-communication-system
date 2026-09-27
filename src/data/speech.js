export function speechLocale(language){return language==='hi'?'hi-IN':language==='kn'?'kn-IN':'en-IN'}

export function configureUtterance({Constructor,text,language,speed,voices=[]}){
  const utterance=new Constructor(text);
  const locale=speechLocale(language);
  utterance.lang=locale;
  utterance.rate=speed||1;
  utterance.voice=voices.find(voice=>voice.lang?.toLowerCase().startsWith(locale.toLowerCase()))||voices.find(voice=>voice.lang?.toLowerCase().startsWith(language))||voices.find(voice=>voice.default)||voices[0]||null;
  return utterance;
}
