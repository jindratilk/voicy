export type Settings = {engine: 'denoise'|'restore'|'mossformer'|'studio'|'auk'; mode: 'natural'|'strong'; amount: number; level: boolean}
export type AudioInfo = {duration:number;sample_rate:number;peaks:number[];peak_db:number;rms_db:number;clipped_samples:number}
export type Job = {id:string;name:string;created:number;status:string;message:string;progress:number;original?:AudioInfo;enhanced?:AudioInfo;warnings?:string[];elapsed?:number;compare_gain?:number;settings?:Settings;result_settings?:Settings;revision?:number}
export const busy = (j:Job|null) => !!j && ['queued','analyzing','enhancing'].includes(j.status)
export async function api<T>(path:string, init?:RequestInit):Promise<T> {
 const response=await fetch(`/api${path}`,init)
 if(!response.ok) {const err=await response.json().catch(()=>({detail:'The local app could not complete this request.'})); throw new Error(typeof err.detail==='string'?err.detail:'Please check the selected settings.')}
 return response.status===204 ? undefined as T : response.json()
}
export const audioUrl=(j:Job,kind:string)=>`/api/jobs/${j.id}/audio/${kind}?v=${j.revision||0}`
export function clock(t:number) {return `${Math.floor(t/60)}:${Math.floor(t%60).toString().padStart(2,'0')}`}
