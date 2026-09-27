import test from 'node:test';
import assert from 'node:assert/strict';
import {configureUtterance,speechLocale} from '../src/data/speech.js';

class FakeUtterance{constructor(text){this.text=text}}
test('speech locale selects Indian locale for supported interface languages',()=>{
 assert.equal(speechLocale('en'),'en-IN');assert.equal(speechLocale('hi'),'hi-IN');assert.equal(speechLocale('kn'),'kn-IN');assert.equal(speechLocale('unknown'),'en-IN');
});
test('speech selects matching voice, rate, and safe fallback when unavailable',()=>{
 const voices=[{lang:'en-US',name:'English fallback'},{lang:'hi-IN',name:'Hindi'}];
 const hindi=configureUtterance({Constructor:FakeUtterance,text:'नमस्ते',language:'hi',speed:0.8,voices});
 assert.equal(hindi.voice.name,'Hindi');assert.equal(hindi.lang,'hi-IN');assert.equal(hindi.rate,0.8);
 const kannada=configureUtterance({Constructor:FakeUtterance,text:'ನಮಸ್ಕಾರ',language:'kn',speed:1,voices});
 assert.equal(kannada.voice.name,'English fallback');
});
