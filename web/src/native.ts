export const native = '__TAURI_INTERNALS__' in window
export async function invoke<T>(command:string, args?:Record<string,unknown>):Promise<T> {
 const api=await import('@tauri-apps/api/core');return api.invoke<T>(command,args)
}
export async function onNativeEvent<T>(name:string, handler:(payload:T)=>void) {
 if(!native)return ()=>{}
 const {listen}=await import('@tauri-apps/api/event');return listen<T>(name,event=>handler(event.payload))
}
