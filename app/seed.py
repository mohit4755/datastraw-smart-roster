"""Reproducible fictional data; refuses to overwrite an occupied workspace."""
from app.store import initialize, transaction

def sample():
    from app.models import MODELS
    employees=[{'id':i,'name':f'Demo Employee {i:02}','pod_id':min((i-1)//11+1,3),'process_ids':[1,2] if i<=20 else [1,2,3], 'weekly_off':i%7,'max_work_days':26,'active':True} for i in range(1,34)]
    brands=[{'id':i,'name':f'Brand {i:02}','pod_id':min((i-1)//11+1,3) if i<=20 else (2 if i<=22 else 3),'operating_weekdays':list(range(7)) if i%3 else list(range(6)), 'holidays_closed':i%3!=1,'holiday_dates':['2026-11-12'] if i==2 else []} for i in range(1,26)]
    demands=[]
    for i in range(1,21):
        demands.append({'id':i,'brand_id':i,'process_id':1,'employee_ids':[i],'min_staff':1})
    # Same dedicated employee covers both processes in a single daily brand shift.
    demands.append({'id':26,'brand_id':1,'process_id':2,'employee_ids':[1],'min_staff':1,'operating_weekdays':list(range(6)),'holidays_closed':True})
    pools={21:[21,22],22:[21,22],23:[23,24],24:[25,26,27],25:[28,29,30]}
    for i,pool in pools.items():
        demands.append({'id':i,'brand_id':i,'process_id':1,'employee_ids':pool[:2],'min_staff':1 if i!=24 else 2,'staffing_by_weekday':[2,1,1,1,1,1,1] if i==21 else []})
        demands.append({'id':i+10,'brand_id':i,'process_id':2,'employee_ids':pool[1:],'min_staff':1,'operating_weekdays':list(range(6)),'holidays_closed':True})
    demands.append({'id':36,'brand_id':25,'process_id':3,'employee_ids':[30],'min_staff':1,'operating_weekdays':list(range(6))})
    result={'employees':employees,'pods':[{'id':i,'name':n,'lead_employee_id':1 if i==1 else 12 if i==2 else 23} for i,n in enumerate(['Customer Experience','Commerce','Operations'],1)],'processes':[{'id':1,'name':'Customer Support'},{'id':2,'name':'Abandoned Cart Conversions'},{'id':3,'name':'NDR'}],'brands':brands,'demands':demands,'leaves':[{'id':1,'employee_id':1,'start':'2026-11-03','end':'2026-11-04','status':'approved','kind':'leave'},{'id':2,'employee_id':12,'start':'2026-11-09','end':'2026-11-11','status':'approved','kind':'comp_off'}],'holidays':[{'id':1,'name':'Demo company holiday','day':'2026-11-06'}],'rosters':{}}
    for kind,model in MODELS.items(): result[kind]=[model.model_validate(r).model_dump(mode='json') for r in result[kind]]
    return result
if __name__=='__main__':
    initialize()
    with transaction() as s:
        if any(s[k] for k in ['employees','brands','rosters']): raise SystemExit('Workspace is not empty; seed skipped')
        s.update(sample())
    print('Seeded 33 fictional employees, 3 pods, 25 brands (80% single-resource), 3 processes.')
