import {existsSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {delimiter,resolve} from 'node:path';
const python=process.env.PYTHON||'python3';
const localDeps=resolve('work/python-deps');
const pythonPath=[existsSync(localDeps)?localDeps:'',process.env.PYTHONPATH||''].filter(Boolean).join(delimiter);
const result=spawnSync(python,['-m','unittest','discover','-s','backend/tests','-v'],{stdio:'inherit',env:{...process.env,PYTHONPATH:pythonPath}});
if(result.error){console.error(result.error.message);process.exit(1)}
process.exit(result.status??1);
