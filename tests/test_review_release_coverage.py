from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
def exe(p,s):
 p.write_text("#!/bin/bash\n"+s);p.chmod(0o755)
with tempfile.TemporaryDirectory() as td:
 d=Path(td);(d/"bin").mkdir();(d/"aux").mkdir()
 env=os.environ.copy();env.update(PATH=str(d/"bin")+":"+env["PATH"],VERITAS_ANALYSIS_TYPE="AP_DISP",EVNDISPSYS=td,VERITAS_EVNDISP_AUX_DIR=str(d/"aux"),VERITAS_USER_DATA_DIR=td)
 # Plotting coverage: every supplied cut x epoch x atmosphere must invoke ROOT.
 (d/'params').write_text('* VERSION v492\n* SIMTYPE SIM\n* EPOCH V6_2024_2025w\n* EPOCH V6_2025_2025s\n* ATMOSPHERE 61\n* ATMOSPHERE 62\n* CUT Soft soft\n* CUT Hard hard\n* MC_ZE 20\n* MC_WOFF 0.5\n* MC_NSB 100\n* MC_AZ 0\n')
 for cut in ['Soft','Hard']:
  for epoch in ['V6_2024_2025w','V6_2025_2025s']:
   for at in [61,62]:
    p=d/f'irfs/v492/AP/SIM/{epoch}_ATM{at}_gamma/EffectiveAreas_Cut-{cut}_DISP';p.mkdir(parents=True);(p/f'EffArea-SIM-{epoch}-ID0-Ze20deg-0.5wob-100-Cut-{cut}.root').write_text('root')
 exe(d/'bin/root', 'echo "$*" >> "$ROOT_TRACE"\npython - "$@" <<\'PY\'\nimport re, sys\nfrom pathlib import Path\narguments = re.findall(r\'"([^"]*)"\', sys.argv[-1])\noutput = Path(arguments[9]) / (arguments[1] + ".png")\noutput.write_text(arguments[3])\nPY\n');env.update(VERITAS_IRFPRODUCTION_DIR=str(d/'irfs'),RELEASE_OUTPUT_DIR=str(d/'plots'),ROOT_TRACE=str(d/'root.trace'))
 p=ROOT/'EventDisplay_ReleaseTests_code/release_tests/montecarlo/irf_plotting/irf_plotting.sh'
 res=subprocess.run(['bash',str(p),str(d/'params')],env=env,cwd=d,stdout=subprocess.PIPE,text=True,stderr=subprocess.STDOUT);assert res.returncode==0,res.stdout
 assert len((d/'root.trace').read_text().splitlines())==8,res.stdout
 assert '8 tested; 0' in res.stdout,res.stdout
 plots = list((d/'plots').rglob('*.png'))
 assert len(plots) == 8, 'Atmosphere-specific plots were overwritten'
 assert {plot.read_text() for plot in plots} == {'61', '62'}
 for plot in plots:
  assert ('ATM'+plot.read_text()) in str(plot.parent)
 print('PASS release plotting covers 2 cuts x 2 epochs x 2 atmospheres')
 # Lookup sanity checker requires successful executable AND marker AND output.
 aux=d/'aux';(aux/'IRFVERSION').write_text('v492\n');(aux/'Tables').mkdir();(aux/'Tables/table.root').write_text('table');(d/'reference.root').write_text('events')
 exe(d/'bin/mscw_energy','[[ $MODE == producer-fail ]] && exit 9\nfor arg in "$@";do case $arg in -outputfile) next=1;;*) if [[ $next == 1 ]]; then [[ $MODE != missing ]] && printf new > "$arg";next=0;fi;;esac;done\n[[ $MODE != log-fail ]] && echo "...survived test of table file!"\nexit 0\n')
 p=ROOT/'EventDisplay_ReleaseTests_code/release_tests/lookuptable-testing/test_tables.sh'
 for mode in ['producer-fail','missing','log-fail','success']:
  env['MODE']=mode;res=subprocess.run(['bash',str(p),str(d/'reference.root')],env=env,cwd=d,stdout=subprocess.PIPE,text=True,stderr=subprocess.STDOUT);assert (res.returncode==0)==(mode=='success'),(mode,res.stdout)
 print('PASS lookup executable/missing-output/missing-sanity-marker failures')
