"""Archive only immutable original Voicy bytes, with an independent fresh-host verifier."""
import importlib.util,json,os,shutil
from pathlib import Path
S=Path(os.environ['VOICY_SOURCE_DIR']);spec=importlib.util.spec_from_file_location('voicy_protocol',S/'hosted-corrected-release.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
REPO='jindratilk/voicy';ROOT=H.ROOT;REPORTS=H.REPORTS
EXPECTED='7e23011e3169adff45be0126d1af9bed2e25338e15b69beb5550ec31d8fa3081';SIZE=6513528823
URL='https://voicy-downloads.internal-3bf.workers.dev/download?v=0.3.2'

def tag():return 'v0.3.2-original-archive-'+os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']
def fresh():
 H.require(not ROOT.exists(),'Preserve existing workspace');ROOT.mkdir(mode=0o700);REPORTS.mkdir()
def archive():
 fresh();H.require(shutil.disk_usage(ROOT).free>9_000_000_000,'Insufficient backup workspace')
 path=ROOT/'original.dmg';H.run('curl','--fail','--silent','--show-error','--location','--retry','3','--max-time','1200',URL,'--output',str(path))
 H.require(path.stat().st_size==SIZE and H.digest(path)==EXPECTED,'Original source changed; preserve Mac cache')
 refs=H.api('repos/'+REPO+'/git/matching-refs/tags/'+tag())
 if not refs:H.api('repos/'+REPO+'/git/refs',{'ref':'refs/tags/'+tag(),'sha':os.environ['GITHUB_SHA']},'POST')
 ref=H.api('repos/'+REPO+'/git/ref/tags/'+tag());H.require(ref['object']['sha']==os.environ['GITHUB_SHA'],'Wrong archive source tag')
 release=H.api('repos/'+REPO+'/releases',{'tag_name':tag(),'target_commitish':os.environ['GITHUB_SHA'],'name':'Original Voicy 0.3.2 byte archive','body':'Internal backup of the exact original legacy artifact. Not a consumer download or a working release. No artifact is overwritten.','draft':True,'prerelease':True,'make_latest':'false'},'POST')
 H.require(release['draft'] is True and release['target_commitish']==os.environ['GITHUB_SHA'],'Wrong backup release')
 parts=[];offset=0
 with path.open('rb') as source:
  for number in range(1,5):
   length=min(1_800_000_000,SIZE-offset);p=ROOT/('Original-Voicy-0.3.2-arm64.dmg.part'+str(number).zfill(3))
   with p.open('wb') as out:
    left=length
    while left:
     b=source.read(min(left,8*1024*1024));H.require(bool(b),'Truncated original');out.write(b);left-=len(b)
   sha=H.digest(p);H.run('gh','release','upload',tag(),str(p),'--repo',REPO)
   current=H.api('repos/'+REPO+'/releases/'+str(release['id']));a=next(a for a in current['assets'] if a['name']==p.name)
   H.require(a['size']==length and a['digest']=='sha256:'+sha and a['state']=='uploaded','Backup upload differs')
   parts.append({'id':a['id'],'name':p.name,'offset':offset,'bytes':length,'sha256':sha});offset+=length;p.unlink()
 H.require(offset==SIZE,'Backup coverage differs')
 data={'release_id':release['id'],'tag':tag(),'producer_source':os.environ['GITHUB_SHA'],'original_url':URL,'artifact_sha256':EXPECTED,'artifact_bytes':SIZE,'parts':parts,'consumer_release':False}
 m=ROOT/'ORIGINAL-MANIFEST.json';H.save(m,data);sha=H.digest(m);H.run('gh','release','upload',tag(),str(m),'--repo',REPO)
 a=next(a for a in H.api('repos/'+REPO+'/releases/'+str(release['id']))['assets'] if a['name']==m.name);H.require(a['digest']=='sha256:'+sha,'Backup manifest differs')
 proof={**data,'manifest_id':a['id'],'manifest_sha256':sha,'manifest_bytes':m.stat().st_size};H.save(REPORTS/'ORIGINAL-ARCHIVE.json',proof)
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as out:
  for k,v in {'release_id':release['id'],'manifest_id':a['id'],'manifest_hash':sha,'manifest_bytes':m.stat().st_size}.items():out.write(k+'='+str(v)+'\n')

def verify():
 import hashlib
 fresh();release_id=int(os.environ['VOICY_RELEASE_ID']);r=H.api('repos/'+REPO+'/releases/'+str(release_id))
 H.require(r['draft'] is True and r['prerelease'] is True and r['tag_name']==tag() and r['target_commitish']==os.environ['GITHUB_SHA'],'Wrong archived original release')
 m=ROOT/'ORIGINAL-MANIFEST.json';H.asset(int(os.environ['VOICY_MANIFEST_ID']),m,os.environ['VOICY_MANIFEST_HASH'],int(os.environ['VOICY_MANIFEST_BYTES']));data=json.loads(m.read_text())
 H.require(data['release_id']==release_id and data['producer_source']==os.environ['GITHUB_SHA'] and data['artifact_sha256']==EXPECTED and data['artifact_bytes']==SIZE and len(data['parts'])==4,'Wrong original backup identity')
 whole=hashlib.sha256();offset=0
 for n,part in enumerate(data['parts'],1):
  H.require(part['name']=='Original-Voicy-0.3.2-arm64.dmg.part'+str(n).zfill(3) and part['offset']==offset and 0<part['bytes']<=1_800_000_000,'Unsafe original backup part')
  p=ROOT/part['name'];H.asset(part['id'],p,part['sha256'],part['bytes'])
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):whole.update(b)
  offset+=part['bytes'];p.unlink()
 H.require(offset==SIZE and whole.hexdigest()==EXPECTED,'Independent archived-original reconstruction differs')
 H.save(REPORTS/'ORIGINAL-INDEPENDENT-VERIFICATION.json',{'release_id':release_id,'manifest_asset_id':int(os.environ['VOICY_MANIFEST_ID']),'manifest_sha256':os.environ['VOICY_MANIFEST_HASH'],'original_bytes':SIZE,'original_sha256':EXPECTED,'all_remote_parts_and_concatenated_bytes_verified_on_new_host':True,'local_Mac_original_cache_may_be_archived':True,'consumer_release':False})

if __name__=='__main__':
 phase=os.sys.argv[1]
 try:
  H.require(os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_REF')=='refs/heads/codex/clean-mac-qualification','Wrong Voicy-only archival scope')
  {'archive':archive,'verify':verify}[phase]()
 except Exception as error:
  if REPORTS.exists():H.save(REPORTS/'ORIGINAL-ARCHIVE-ERROR.json',{'phase':phase,'error_type':type(error).__name__,**({'message':str(error)} if isinstance(error,H.ReleaseError) else {})})
  print(json.dumps({'phase':phase,'error_type':type(error).__name__}));raise SystemExit(1)
