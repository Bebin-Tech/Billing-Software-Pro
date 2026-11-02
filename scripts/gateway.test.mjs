import {test} from 'node:test';
import assert from 'node:assert/strict';
import handler from '../frontend/api/gateway.js';
function response(){return {headers:{},setHeader(k,v){this.headers[k]=v;},status(s){this.code=s;return this;},json(body){this.body=body;return this;},send(body){this.body=body;return this;}};}
test('missing backend fails explicitly',async()=>{
  delete process.env.BACKEND_URL;const res=response();await handler({headers:{},url:'/api/gateway?path=v1/auth/login'},res);assert.equal(res.code,503);assert.match(res.body.detail,/not configured/);
});
test('gateway forwards auth, query, body and rotated cookies',async()=>{
  process.env.BACKEND_URL='https://backend.example.com';const original=globalThis.fetch;
  globalThis.fetch=async(url,options)=>{
    assert.equal(String(url),'https://backend.example.com/api/v1/auth/login?q=test');assert.equal(options.headers['x-company-id'],'1');assert.equal(options.body,'{"email":"qa@example.com"}');
    return new Response('{"ok":true}',{status:200,headers:{'content-type':'application/json','set-cookie':'refresh_token=test; HttpOnly; Secure; Path=/api/v1/auth'}});
  };
  try{const res=response();await handler({headers:{'x-company-id':'1'},method:'POST',url:'/api/gateway?path=v1/auth/login&q=test',body:{email:'qa@example.com'}},res);assert.equal(res.code,200);assert.equal(res.headers['Set-Cookie'].length,1);}finally{globalThis.fetch=original;delete process.env.BACKEND_URL;}
});
test('gateway rejects path traversal',async()=>{
  process.env.BACKEND_URL='https://backend.example.com';try{const res=response();await handler({headers:{},url:'/api/gateway?path=v1/../secrets'},res);assert.equal(res.code,404);}finally{delete process.env.BACKEND_URL;}
});
