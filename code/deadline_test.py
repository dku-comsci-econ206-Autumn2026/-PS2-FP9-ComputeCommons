from pathlib import Path
import sys,json,itertools,random
sys.path.insert(0,str(Path(__file__).resolve().parent))
from robot_model import allocate,deadline

def actual_utility(true,out,i):
    finish=next((r['finish_ms'] for r in out['details'] if r['id']==true[i]['id']),None)
    return true[i]['value']*int(finish is not None and finish<=deadline(true[i]))-out['payments'][i]

def run():
    rng=random.Random(20614);checks=0;max_gain=0;witness=None
    for batch in range(300):
        jobs=[dict(id=str(i),value=rng.randint(1,12),eligible=int(i==2),service_ms=rng.choice([1,2]),buffer_steps=rng.randint(1,6),period_ms=1,tolerance_mm=100,speed_mm_s=0,network_ms=0) for i in range(3)]
        credit=rng.choice([0,2]); honest=allocate(jobs,credit=credit,horizon=6)
        for i in range(3):
            base=actual_utility(jobs,honest,i)
            for d,b in itertools.product(range(1,8),range(14)):
                reports=[dict(j) for j in jobs];reports[i]['buffer_steps']=d
                bids=[j['value'] for j in jobs];bids[i]=b
                out=allocate(reports,bids,credit=credit,horizon=6)
                gain=actual_utility(jobs,out,i)-base;checks+=1
                if gain>max_gain:max_gain=gain;witness=dict(jobs=jobs,i=i,deadline=d,bid=b,gain=gain)
    assert max_gain<=1e-9
    result=dict(version='final-fp9-2026-10-21',seed=20614,batches=300,agents=3,deviations=checks,max_profitable_gain=max_gain,witness=witness,scope='Joint value/deadline reports only; execution uses reported EDF order but utility uses actual deadlines; fixed public service times, rivals, eligibility and finite values. Late winners still pay. Not a test of general telemetry fraud.')
    true=[dict(id=k,value=v,eligible=0,service_ms=p,buffer_steps=300,period_ms=1,tolerance_mm=100,speed_mm_s=0,network_ms=0) for k,v,p in [('A',10,200),('B',9,100),('C',8,100)]]
    honest=allocate(true,horizon=300); reported=[dict(j) for j in true];reported[0]['service_ms']=100
    false=allocate(reported,horizon=300);elapsed=0;actual=[]
    for k in false['order']:
        j=next(j for j in true if j['id']==k);elapsed+=j['service_ms'];actual.append(dict(id=k,finish_ms=elapsed,timely=elapsed<=deadline(j)))
    result['duration_counterexample']=dict(true_service_ms=[200,100,100],reported_service_ms=[100,100,100],values=[10,9,8],horizon=300,honest=honest,reported_allocation=false,actual_execution=actual,liar_actual_utility=10-false['payments'][0],honest_utility=honest['utilities'][0],gain=10-false['payments'][0]-honest['utilities'][0])
    assert result['duration_counterexample']['gain']==8
    Path(__file__).with_name('deadline_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':run()
