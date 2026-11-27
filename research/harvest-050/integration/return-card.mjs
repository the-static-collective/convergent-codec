// HARVEST return v1: local, explicit, private metadata handoff. No execution or network.
import {createHash} from 'node:crypto';
import {openSync,readSync,closeSync,fstatSync,constants} from 'node:fs';
import {pathToFileURL} from 'node:url';
export const SOURCE='8880092d729e8f9f01ad5bd34b1d2e158fc109fb';
const KEYS='schema source_commit manifest_pin receipt_sha256 plan_pin verified_files direct regenerated readback classification authority admission'.split(' ').sort();
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const count=(x,max)=>Number.isSafeInteger(x)&&x>=0&&x<=max;
const need=(ok,msg)=>{if(!ok)throw Error(msg)};
export const digest=b=>createHash('sha256').update(b).digest('hex');
function localBytes(path,max){
 const fd=openSync(path,constants.O_RDONLY|(constants.O_NOFOLLOW??0)|(constants.O_NONBLOCK??0));
 try{const st=fstatSync(fd);need(st.isFile()&&st.size<=max,'HOLD_FILE_BOUND');const buf=Buffer.alloc(st.size+1);let n=0,k;while(n<buf.length&&(k=readSync(fd,buf,n,buf.length-n,null))>0)n+=k;need(n===st.size,'HOLD_FILE_CHANGED');return buf.subarray(0,n)}finally{closeSync(fd)}
}
export function inspect(bytes,pin){
 need(Buffer.isBuffer(bytes)&&bytes.length<=4096&&hex(pin)&&digest(bytes)===pin,'HOLD_CARD_PIN');
 const p=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
 need(p&&typeof p==='object'&&!Array.isArray(p)&&Object.keys(p).sort().join('|')===KEYS.join('|'),'HOLD_CARD_FIELDS');
 need(bytes.equals(Buffer.from(JSON.stringify(Object.fromEntries(KEYS.map(k=>[k,p[k]])))+'\n')),'HOLD_NONCANONICAL_CARD');
 need(p.schema==='harvest.return/v1'&&p.source_commit===SOURCE&&p.classification==='PRIVATE_OPERATOR_HANDOFF'&&p.authority==='NONE'&&p.admission==='none'&&p.readback==='matched','HOLD_CARD_CONTRACT');
 need([p.manifest_pin,p.receipt_sha256,p.plan_pin].every(hex)&&count(p.verified_files,4096)&&count(p.direct,32768)&&count(p.regenerated,32768)&&p.direct+p.regenerated<=32768,'HOLD_CARD_VALUES');
 return {schema:'harvest.held-return/v1',status:'HOLD_FOR_OPERATOR_REVIEW',card_sha256:pin,source_commit:SOURCE,manifest_pin:p.manifest_pin,receipt_sha256:p.receipt_sha256,verified_files:p.verified_files,direct:p.direct,regenerated:p.regenerated,authority:'NONE',admission:'none',executed:false};
}
export function contact(bytes,pin,now=new Date().toISOString()){
 const r=inspect(bytes,pin);need(typeof now==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(now)&&Number.isFinite(Date.parse(now)),'HOLD_TIME');
 return {schema:'memento.understory-record/v0',family:'contact',id:'harvest-'+pin,observer:'local-harvest-operator',recorded_at:now,sensed_at:now,occurrence_ref:'sha256:'+pin,evidence_refs:['sha256:'+r.receipt_sha256,'sha256:'+r.manifest_pin,'https://github.com/the-static-collective/convergent-codec/tree/'+SOURCE+'/research/harvest-050'],note:'Private metadata handoff; receipt claim, not independent verification or canon.'};
}
export function transport(path,pin,size){
 need(hex(pin)&&count(size,25*1024*1024)&&size>0,'HOLD_TRANSPORT_BOUND');const bytes=localBytes(path,25*1024*1024);need(bytes.length===size&&digest(bytes)===pin,'HOLD_TRANSPORT_MISMATCH');
 return {schema:'harvest.transport-check/v1',status:'BYTES_MATCH_EXPECTED_PIN',sha256:pin,bytes:size,authority:'NONE',admission:'none',uploaded:false};
}
function main(args){const [mode,path,pin,size]=args;need(path&&pin,'usage: node return-card.mjs jarvis|memento CARD PIN OR fileport FILE PIN BYTES');let r;if(mode==='fileport'){need(args.length===4&&/^\d+$/.test(size),'HOLD_SIZE');r=transport(path,pin,Number(size))}else{need(args.length===3&&['jarvis','memento'].includes(mode),'HOLD_MODE');const b=localBytes(path,4096);r=mode==='jarvis'?inspect(b,pin):contact(b,pin)}console.log(JSON.stringify(r,null,2))}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{main(process.argv.slice(2))}catch(e){console.error('HOLD:',e.message);process.exitCode=2}}
