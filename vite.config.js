import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
const apiTarget=process.env.AAC_API_PROXY||'http://127.0.0.1:5000';
const securityHeaders={
 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:; worker-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
 'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer'
};
export default defineConfig({plugins:[react()],server:{proxy:{'/api':{target:apiTarget,changeOrigin:true}}},preview:{proxy:{'/api':{target:apiTarget,changeOrigin:true}},headers:securityHeaders}});
