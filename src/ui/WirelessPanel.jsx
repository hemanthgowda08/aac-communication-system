import React,{useEffect,useState} from 'react';
import {Bluetooth,Check,Link2,Unplug,Wifi,WifiOff} from 'lucide-react';

const UART_SERVICE='6e400001-b5a3-f393-e0a9-e50e24dcca9e';
const UART_TX='6e400002-b5a3-f393-e0a9-e50e24dcca9e';
export default function WirelessPanel({message,onTransmit}){
 const supported=typeof navigator!=='undefined'&&'bluetooth'in navigator;
 const [device,setDevice]=useState(null),[characteristic,setCharacteristic]=useState(null),[status,setStatus]=useState('disconnected'),[error,setError]=useState(''),[simulation,setSimulation]=useState(false),[sent,setSent]=useState(false);
 useEffect(()=>{if(!device)return;const disconnect=()=>{setStatus('disconnected');setCharacteristic(null);setDevice(null);setSimulation(false)};device.addEventListener('gattserverdisconnected',disconnect);return()=>{device.removeEventListener('gattserverdisconnected',disconnect);if(device.gatt?.connected)device.gatt.disconnect()}},[device]);
 const connect=async()=>{
  setError('');setStatus('connecting');setSent(false);
  if(!supported){setStatus('disconnected');setError('Web Bluetooth is not available here. Use Wireless demo to explore the flow.');return}
  try{const chosen=await navigator.bluetooth.requestDevice({filters:[{services:[UART_SERVICE]}]});setDevice(chosen);const server=await chosen.gatt.connect();const service=await server.getPrimaryService(UART_SERVICE);const tx=await service.getCharacteristic(UART_TX);setCharacteristic(tx);setStatus('connected')}
  catch(err){setStatus('disconnected');setDevice(null);setCharacteristic(null);setError(err.name==='NotFoundError'?'No compatible UART device was selected.':err.name==='SecurityError'?'Bluetooth needs a secure page (HTTPS or localhost).':`Could not connect: ${err.message||'device unavailable'}`)}
 };
 const disconnect=()=>{if(device?.gatt?.connected)device.gatt.disconnect();setDevice(null);setCharacteristic(null);setStatus('disconnected');setSimulation(false);setError('')};
 const demo=()=>{setDevice(null);setCharacteristic(null);setSimulation(true);setStatus('connected');setError('');setSent(false)};
 const send=async()=>{if(!message.trim())return;setError('');setSent(false);try{if(simulation){await new Promise(resolve=>setTimeout(resolve,300));setSent(true);onTransmit?.();return}if(!characteristic)throw new Error('Connect a compatible UART device first.');await characteristic.writeValue(new TextEncoder().encode(message.trim()).slice(0,180));setSent(true);onTransmit?.()}catch(err){setError(`Message was not sent: ${err.message||'wireless error'}`)}};
 const connected=status==='connected';
 return <section className="wireless-card card"><div className="wireless-heading"><span className={`wireless-icon ${connected?'connected':''}`}><Bluetooth size={18}/></span><div><b>Wireless communication</b><small>{supported?'Web Bluetooth available in this browser':'Bluetooth unavailable in this browser'}</small></div><span className={`connection-status ${connected?'connected':''}`}><i/>{simulation?'Demo connected':connected?(device?.name||'Connected'):'Not connected'}</span></div>
  <p>Connect a compatible BLE UART device to send a short message. Uses the Nordic UART Service profile; browser and device support varies.</p>
  <div className="wireless-actions">{connected?<button className="outline-action" onClick={disconnect}><Unplug size={15}/>Disconnect</button>:<button className="outline-action" onClick={connect}><Bluetooth size={15}/>{status==='connecting'?'Connecting…':'Connect Bluetooth'}</button>}{!connected&&<button className="demo-button" onClick={demo}><Wifi size={15}/>Try wireless demo</button>}{connected&&<button className="speak-button" onClick={send} disabled={!message.trim()}><Link2 size={15}/>{simulation?'Simulate send':'Send message'}</button>}</div>
  {error&&<div className="wireless-feedback error" role="status"><WifiOff size={14}/>{error}</div>}{sent&&<div className="wireless-feedback success" role="status"><Check size={14}/>{simulation?'Demo message delivered through simulated BLE flow.':'Message sent to the connected BLE UART device.'}</div>}
 </section>
}
