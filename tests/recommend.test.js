import test from 'node:test';
import assert from 'node:assert/strict';
import {categories,items,starterPhrases} from '../src/data/content.js';
import {recommend} from '../src/data/recommend.js';

test('catalog has populated categories and recognizable demo content',()=>{
  assert.ok(categories.length>=8);
  assert.ok(items.some(item=>item.id==='water'));
  assert.ok(items.some(item=>item.id==='emergency'));
  assert.ok(starterPhrases.length>=4);
});
test('I want suggests useful words in English and Hindi',()=>{
  assert.deepEqual(recommend('I want').map(item=>item.id).slice(0,3),['water','food','go']);
  assert.equal(recommend('I want','hi')[0].label,'पानी');
});
test('I need and I am use deterministic local mappings',()=>{
  assert.ok(recommend('I need').some(item=>item.id==='help'));
  assert.ok(recommend('I am').some(item=>item.id==='tired'));
  assert.ok(recommend('please, I need').some(item=>item.id==='doctor'));
});
test('unknown and empty messages return no recommendations',()=>{
  assert.deepEqual(recommend(''),[]);
  assert.deepEqual(recommend('a sentence without a matching context'),[]);
});
