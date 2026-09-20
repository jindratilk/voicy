// @vitest-environment jsdom
import React,{StrictMode} from 'react'
import {render,fireEvent,screen,cleanup,waitFor} from '@testing-library/react'
import {afterEach,beforeEach,describe,it,expect,vi} from 'vitest'
import {Player} from './Player'
import type {Job} from './api'
const {invoke}=vi.hoisted(()=>({invoke:vi.fn()}))
vi.mock('./native',()=>({native:true,invoke}))
const job:Job={id:'a'.repeat(32),name:'Test.wav',created:0,status:'done',message:'',progress:1,compare_gain:2,original:{duration:10,sample_rate:48000,peaks:[.1,.8,.2],peak_db:-2,rms_db:-20,clipped_samples:0},enhanced:{duration:10,sample_rate:48000,peaks:[.2,.7,.1],peak_db:-1,rms_db:-14,clipped_samples:0}}
let play:ReturnType<typeof vi.spyOn>,pause:ReturnType<typeof vi.spyOn>
beforeEach(()=>{
 vi.stubGlobal('ResizeObserver',class{observe(){}disconnect(){}})
 Object.defineProperty(HTMLMediaElement.prototype,'readyState',{configurable:true,get:()=>1})
 Object.defineProperty(HTMLMediaElement.prototype,'duration',{configurable:true,get:()=>10})
 play=vi.spyOn(HTMLMediaElement.prototype,'play').mockImplementation(function(this:HTMLMediaElement){this.dispatchEvent(new Event('play'));return Promise.resolve()})
 pause=vi.spyOn(HTMLMediaElement.prototype,'pause').mockImplementation(function(this:HTMLMediaElement){this.dispatchEvent(new Event('pause'))})
 invoke.mockReset();invoke.mockResolvedValue(true)
})
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals()})
describe('audio comparison',()=>{
 it('uses one metadata-only audio element and retains position while switching',async()=>{
  const {container}=render(<Player job={job}/>);const a=container.querySelector('audio')!
  expect(container.querySelectorAll('audio')).toHaveLength(1);expect(a.preload).toBe('metadata')
  a.currentTime=6;fireEvent.timeUpdate(a);fireEvent.click(screen.getByRole('button',{name:'Play'}));
  fireEvent.click(screen.getByRole('tab',{name:'Original'}));fireEvent.loadedMetadata(a)
  expect(a.currentTime).toBe(6);await waitFor(()=>expect(play).toHaveBeenCalledTimes(2))
  expect(a.volume).toBe(1)
 })
 it('keeps both A/B tabs functional through rapid switches',()=>{
  const {container}=render(<Player job={job}/>);const a=container.querySelector('audio')!
  a.currentTime=4;fireEvent.timeUpdate(a)
  for(let i=0;i<5;i++){fireEvent.click(screen.getByRole('tab',{name:'Original'}));fireEvent.loadedMetadata(a);fireEvent.click(screen.getByRole('tab',{name:'Enhanced'}));fireEvent.loadedMetadata(a)}
  expect(a.currentTime).toBe(4);expect(a.volume).toBe(.5);expect(container.querySelectorAll('audio')).toHaveLength(1)
 })
 it('does not start playback when a history dialog is open',()=>{
  render(<Player job={job} disabled/>);fireEvent(window,new CustomEvent('voicy-player',{detail:'play'}));fireEvent.keyDown(document.body,{code:'Space'});expect(play).not.toHaveBeenCalled()
 })
 it('seeks with the accessible range and leaves the audio playable in StrictMode',()=>{
  const {container}=render(<StrictMode><Player job={job}/></StrictMode>);const a=container.querySelector('audio')!
  fireEvent.change(screen.getByRole('slider'),{target:{value:'3.5'}});expect(a.currentTime).toBe(3.5)
  expect(a.getAttribute('src')).toContain('/enhanced');fireEvent.click(screen.getByRole('button',{name:'Play'}));expect(play).toHaveBeenCalled()
 })
 it('reports a playback failure',async()=>{
  play.mockRejectedValue(new DOMException('Unavailable','NotSupportedError'));render(<Player job={job}/>);fireEvent.click(screen.getByRole('button',{name:'Play'}));expect(await screen.findByRole('alert')).toBeTruthy()
 })
 it('opens only one native export dialog for repeated commands',async()=>{
  let resolve!:(v:boolean)=>void;invoke.mockReturnValue(new Promise<boolean>(r=>resolve=r));render(<Player job={job}/>);
  fireEvent(window,new CustomEvent('voicy-player',{detail:'save'}));fireEvent(window,new CustomEvent('voicy-player',{detail:'save'}));expect(invoke).toHaveBeenCalledTimes(1);resolve(false);await waitFor(()=>expect(screen.getByRole('button',{name:'Export'})).toBeTruthy())
 })
 it('does not expose enhanced playback before a result exists',()=>{
  render(<Player job={{...job,enhanced:undefined}}/>);expect((screen.getByRole('tab',{name:'Enhanced'}) as HTMLButtonElement).disabled).toBe(true)
 })
})
