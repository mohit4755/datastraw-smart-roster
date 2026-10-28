"""Persistent API; all writes serialize on the workspace row in PostgreSQL."""
import os
import secrets
from datetime import date
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from pydantic import ValidationError
from app.models import MODELS, Generate, Edit
from app.store import transaction
from app.engine import generate, validate
from app.seed import sample
router=APIRouter(prefix='/api')

def authorize(authorization: str = Header(default='')):
    token=os.getenv('ADMIN_TOKEN')
    if token and not secrets.compare_digest(authorization, f'Bearer {token}'):
        raise HTTPException(401, detail={'code':'unauthorized','message':'A valid admin token is required for changes'})

def fail(message,code=409): raise HTTPException(code,detail={'code':'validation_error','message':message})

def references(s):
    ids={k:{r['id'] for r in s[k]} for k in MODELS}
    def ref(k,v):
        if v not in ids[k]: fail(f'{k} ID {v} does not exist')
    for pod in s['pods']:
        lead=pod.get('lead_employee_id')
        if lead is not None:
            ref('employees',lead)
            if next(e for e in s['employees'] if e['id']==lead)['pod_id']!=pod['id']: fail('Pod lead must belong to the pod')
    for e in s['employees']:
        ref('pods',e['pod_id'])
        for p in e['process_ids']: ref('processes',p)
    for b in s['brands']: ref('pods',b['pod_id'])
    seen=set()
    for d in s['demands']:
        ref('brands',d['brand_id']); ref('processes',d['process_id'])
        key=(d['brand_id'],d['process_id'])
        if key in seen: fail('Duplicate brand/process demand')
        seen.add(key)
        for eid in d['employee_ids']:
            ref('employees',eid)
            e=next(e for e in s['employees'] if e['id']==eid); b=next(b for b in s['brands'] if b['id']==d['brand_id'])
            if e['pod_id']!=b['pod_id'] or d['process_id'] not in e['process_ids']: fail(f'Employee {eid} is not eligible for demand {d["id"]}')
    for l in s['leaves']: ref('employees',l['employee_id'])

def resource(name):
    if name not in MODELS: raise HTTPException(404,detail='Unknown resource')
    return MODELS[name]

def impact(s):
    return {key:validate(s,r['year'],r['month'],r['slots']) for key,r in s['rosters'].items()}

@router.get('/health')
def health():
    with transaction(): pass
    return {'status':'ok','database':'connected','ai':'disabled','scheduler':'OR-Tools CP-SAT'}

@router.get('/data')
def data():
    with transaction() as s: return {k:s[k] for k in MODELS}

@router.post('/seed',dependencies=[Depends(authorize)],status_code=201)
def seed():
    with transaction() as s:
        if any(s[k] for k in MODELS) or s['rosters']: fail('Workspace is not empty; seed refuses to overwrite data')
        s.update(sample())
    return {'message':'Fictional demonstration workspace initialized'}

@router.post('/rosters/generate',dependencies=[Depends(authorize)],status_code=201)
def generate_roster(body:Generate):
    with transaction() as s:
        key=f'{body.year}-{body.month:02d}'
        try: result=generate(s,body.year,body.month)
        except ValueError as exc: raise HTTPException(503,detail={'code':'solver_unavailable','message':str(exc)}) from exc
        result['revision']=s['rosters'].get(key,{}).get('revision',0)+1
        s['rosters'][key]=result
        return result

@router.get('/rosters/{year}/{month}')
def get_roster(year:int,month:int,employee_id:int|None=None,brand_id:int|None=None,process_id:int|None=None,pod_id:int|None=None):
    with transaction() as s:
        r=s['rosters'].get(f'{year}-{month:02d}')
        if r is None: raise HTTPException(404,detail='Generate this month first')
        result={**r,**validate(s,year,month,r['slots'])}
        ds={d['id']:d for d in s['demands']}; es={e['id']:e for e in s['employees']}
        result['slots']=[x for x in r['slots'] if (employee_id is None or x['employee_id']==employee_id) and (brand_id is None or ds.get(x['demand_id'],{}).get('brand_id')==brand_id) and (process_id is None or ds.get(x['demand_id'],{}).get('process_id')==process_id) and (pod_id is None or es.get(x['employee_id'],{}).get('pod_id')==pod_id)]
        return result

@router.put('/rosters/{year}/{month}',dependencies=[Depends(authorize)])
def edit_roster(year:int,month:int,body:Edit):
    with transaction() as s:
        key=f'{year}-{month:02d}'; r=s['rosters'].get(key)
        if r is None: raise HTTPException(404,detail='Roster not found')
        if body.revision!=r['revision']: fail('Roster changed; reload before editing')
        slots=[x.model_dump(mode='json') for x in body.slots]
        report=validate(s,year,month,slots)
        if body.preview: return report
        if report['conflicts']: raise HTTPException(409,detail={'code':'constraint_violation','message':'Edit rejected; hard constraints would be violated','report':report})
        # Shortages may exist already; never permit a manual edit to increase missing coverage.
        before=validate(s,year,month,r['slots'])
        previous={(v['day'],v['demand_id']):v['missing'] for v in before['shortages']}
        if any(v['missing']>previous.get((v['day'],v['demand_id']),0) for v in report['shortages']):
            raise HTTPException(409,detail={'code':'coverage_reduction','message':'Edit rejected; it creates or worsens a coverage shortage','report':report})
        r.update(slots=slots,revision=r['revision']+1,**report,solver_status='MANUALLY_EDITED',optimal=False)
        return r

@router.get('/impact')
def get_impact():
    with transaction() as s: return impact(s)

@router.get('/{name}')
def list_records(name:str):
    resource(name)
    with transaction() as s: return s[name]

@router.post('/{name}',dependencies=[Depends(authorize)],status_code=201)
def create(name:str,body:dict=Body(...)):
    model=resource(name)
    try: record=model.model_validate(body).model_dump(mode='json')
    except ValidationError as exc: raise HTTPException(422,detail=exc.errors(include_context=False))
    with transaction() as s:
        if any(r['id']==record['id'] for r in s[name]): fail('ID already exists')
        s[name].append(record); references(s)
        return {'record':record,'impact':impact(s)}

@router.put('/{name}/{record_id}',dependencies=[Depends(authorize)])
def update(name:str,record_id:int,body:dict=Body(...),preview:bool=False):
    model=resource(name)
    try: record=model.model_validate(body).model_dump(mode='json')
    except ValidationError as exc: raise HTTPException(422,detail=exc.errors(include_context=False))
    if record['id']!=record_id: fail('ID cannot change',422)
    with transaction() as s:
        index=next((i for i,r in enumerate(s[name]) if r['id']==record_id),None)
        if index is None: raise HTTPException(404,detail='Record not found')
        previous=s[name][index]; s[name][index]=record; references(s); report=impact(s)
        if preview: s[name][index]=previous
        return {'record':record,'impact':report,'preview':preview}

@router.delete('/{name}/{record_id}',dependencies=[Depends(authorize)])
def delete(name:str,record_id:int):
    resource(name)
    with transaction() as s:
        if not any(r['id']==record_id for r in s[name]): raise HTTPException(404,detail='Record not found')
        if name in ('employees','demands') and any(any(x['employee_id' if name=='employees' else 'demand_id']==record_id for x in r['slots']) for r in s['rosters'].values()): fail('Referenced by a saved roster; retain the record for history')
        s[name]=[r for r in s[name] if r['id']!=record_id]; references(s)
        return {'deleted':record_id,'impact':impact(s)}
