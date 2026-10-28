from datetime import date
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import store
from app.engine import generate, validate
from app.seed import sample
from app.models import Brand, Leave

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store,'_engine',store.make_engine(f'sqlite:///{tmp_path}/test.db'))
    store.initialize()
    with TestClient(app) as c:
        assert c.post('/api/seed').status_code==201
        yield c

def test_all_crud_and_transactions(client):
    for kind in ['pods','processes']:
        assert client.post('/api/'+kind,json={'id':99,'name':'New'}).status_code==201
        assert client.put('/api/'+kind+'/99',json={'id':99,'name':'Updated'}).status_code==200
        assert any(r['name']=='Updated' for r in client.get('/api/'+kind).json())
        assert client.delete('/api/'+kind+'/99').status_code==200
    employee={'id':99,'name':'Test Employee','pod_id':1,'weekly_off':6,'process_ids':[1],'max_work_days':25,'active':True}
    assert client.post('/api/employees',json=employee).status_code==201
    assert client.post('/api/employees',json=employee).status_code==409
    assert client.put('/api/employees/99',json={**employee,'name':'Updated'}).status_code==200
    assert client.delete('/api/employees/99').status_code==200
    assert client.post('/api/employees',json={**employee,'pod_id':999}).status_code==409
    assert not any(e['id']==99 for e in client.get('/api/employees').json())

def test_invalid_inputs_and_references(client):
    assert client.post('/api/employees',json={'id':-1}).status_code==422
    assert client.delete('/api/pods/1').status_code==409
    assert client.get('/api/unknown').status_code==404
    assert client.post('/api/rosters/generate',json={'year':2026,'month':13}).status_code==422
    assert client.post('/api/seed').status_code==409
    assert client.post('/api/demands',json={'id':99,'brand_id':1,'process_id':1,'employee_ids':[1],'min_staff':1}).status_code==409
    assert client.post('/api/demands',json={'id':99,'brand_id':1,'process_id':2,'employee_ids':[11],'min_staff':1}).status_code==409

def test_generate_persist_filter_and_constraints(client):
    response=client.post('/api/rosters/generate',json={'year':2026,'month':11})
    assert response.status_code==201
    r=response.json(); assert r['conflicts']==[]; assert r['shortages']; assert not r['valid']
    saved=client.get('/api/rosters/2026/11').json(); assert saved['slots']==r['slots']
    assert len({(s['day'],s['employee_id'],s['demand_id']) for s in r['slots']})==len(r['slots'])
    state=client.get('/api/data').json()
    assert validate(state,2026,11,r['slots'])['conflicts']==[]
    assert all(s['employee_id']==1 for s in client.get('/api/rosters/2026/11?employee_id=1').json()['slots'])
    assert all(s['demand_id']==2 for s in client.get('/api/rosters/2026/11?brand_id=2').json()['slots'])
    assert all(s['day']!='2026-11-06' for s in r['slots'] if s['demand_id']==2)
    assert all(not(s['employee_id']==1 and s['day'] in ['2026-11-03','2026-11-04']) for s in r['slots'])
    for slot in r['slots']:
        e=next(e for e in state['employees'] if e['id']==slot['employee_id'])
        assert date.fromisoformat(slot['day']).weekday()!=e['weekly_off']
    assert client.get('/api/health').json()['database']=='connected'
    assert all(next(d for d in state['demands'] if d['id']==x['demand_id'])['process_id']==2 for x in client.get('/api/rosters/2026/11?process_id=2').json()['slots'])
    assert all(next(e for e in state['employees'] if e['id']==x['employee_id'])['pod_id']==2 for x in client.get('/api/rosters/2026/11?pod_id=2').json()['slots'])

def test_manual_edit_preview_reject_save_and_revision(client):
    r=client.post('/api/rosters/generate',json={'year':2026,'month':11}).json()
    payload={'revision':r['revision'],'slots':r['slots']}
    invalid={**payload,'slots':r['slots']+[r['slots'][0]],'preview':True}
    report=client.put('/api/rosters/2026/11',json=invalid).json()
    assert any('duplicate assignment' in c.get('reasons',[]) for c in report['conflicts'])
    invalid['preview']=False
    assert client.put('/api/rosters/2026/11',json=invalid).status_code==409
    assert client.put('/api/rosters/2026/11',json={**payload,'slots':r['slots'][1:]}).status_code==409
    result=client.put('/api/rosters/2026/11',json=payload)
    assert result.status_code==200 and result.json()['revision']==2
    assert client.put('/api/rosters/2026/11',json=payload).status_code==409
    assert client.get('/api/rosters/2026/11').json()['revision']==2

def test_availability_impact_preview_and_save(client):
    r=client.post('/api/rosters/generate',json={'year':2026,'month':11}).json()
    slot=r['slots'][0]; e=next(e for e in client.get('/api/employees').json() if e['id']==slot['employee_id'])
    changed={**e,'active':False}
    result=client.put(f'/api/employees/{e["id"]}?preview=true',json=changed)
    assert result.status_code==200
    assert result.json()['impact']['2026-11']['conflicts']
    assert next(x for x in client.get('/api/employees').json() if x['id']==e['id'])['active']
    assert client.put(f'/api/employees/{e["id"]}',json=changed).status_code==200
    assert client.get('/api/rosters/2026/11').json()['conflicts']
    assert client.get('/api/impact').json()['2026-11']['conflicts']

def test_auth(client,monkeypatch):
    monkeypatch.setenv('ADMIN_TOKEN','test-token')
    assert client.post('/api/pods',json={'id':99,'name':'New'}).status_code==401
    assert client.post('/api/pods',json={'id':99,'name':'New'},headers={'Authorization':'Bearer test-token'}).status_code==201

def test_cp_sat_resolves_greedy_trap_and_deterministic():
    state=sample(); state['employees']=state['employees'][:3]
    for e in state['employees']: e['weekly_off']=6; e['max_work_days']=31
    state['brands']=state['brands'][:1]; state['brands'][0]['operating_weekdays']=list(range(6)); state['leaves']=[];state['holidays']=[]
    state['demands']=[{'id':1,'brand_id':1,'process_id':1,'employee_ids':[1,2],'min_staff':1},{'id':2,'brand_id':1,'process_id':2,'employee_ids':[1,3],'min_staff':1}]
    a=generate(state,2026,11);b=generate(state,2026,11)
    assert a==b and a['valid']
    assert a['coverage_filled']==a['coverage_required']

def test_brand_holiday_and_monthly_limit():
    state=sample();state['employees'][0]['max_work_days']=1
    r=generate(state,2026,11)
    assert r['workload']['1']<=1
    assert not any(x['demand_id']==2 and x['day']=='2026-11-12' for x in r['slots'])
    assert any('monthly work limit reached' in c['reasons'] for s in r['shortages'] for c in s['candidates'])

def test_validated_dates_and_weekdays():
    with pytest.raises(ValueError): Brand(id=1,name='Bad',pod_id=1,operating_weekdays={9})
    with pytest.raises(ValueError): Leave(id=1,employee_id=1,start='2026-11-10',end='2026-11-01')

def test_original_pdf_seed_patterns():
    s=sample()
    assert len(s['employees'])>=30
    pools={b['id']:{eid for d in s['demands'] if d['brand_id']==b['id'] for eid in d['employee_ids']} for b in s['brands']}
    assert sum(len(v)==1 for v in pools.values())/len(pools)==.8
    assert all(2<=len(v)<=3 for v in pools.values() if len(v)>1)
    from app.api import references
    references(s)
    assert all(p['lead_employee_id'] for p in s['pods'])
    assert any(l['kind']=='comp_off' for l in s['leaves'])

def test_process_calendar_daily_staffing_and_bundled_brand_shift():
    s=sample();s['brands']=s['brands'][:1];s['employees']=s['employees'][:2]
    for e in s['employees']:e['weekly_off']=6
    s['leaves']=[];s['holidays']=[]
    s['demands']=[{'id':1,'brand_id':1,'process_id':1,'employee_ids':[1],'min_staff':1}, {'id':2,'brand_id':1,'process_id':2,'employee_ids':[1,2],'min_staff':1,'operating_weekdays':[0,1,2,3,4],'staffing_by_weekday':[2,1,1,1,1,0,0]}]
    slots=[{'day':'2026-11-02','employee_id':1,'demand_id':1},{'day':'2026-11-02','employee_id':1,'demand_id':2},{'day':'2026-11-02','employee_id':2,'demand_id':2}]
    r=validate(s,2026,11,slots)
    assert r['conflicts']==[] and r['workload']['1']==1
    assert not any(x['day']=='2026-11-02' for x in r['shortages'])
    assert not any(x['demand_id']==2 and x['day']=='2026-11-07' for x in r['shortages'])
    s['brands'].append({**s['brands'][0],'id':2})
    s['demands'].append({'id':3,'brand_id':2,'process_id':1,'employee_ids':[1],'min_staff':1})
    assert any(x['type']=='double_booking' for x in validate(s,2026,11,slots+[{'day':'2026-11-02','employee_id':1,'demand_id':3}])['conflicts'])

def test_comp_off_and_daily_staffing_validation(client):
    assert client.post('/api/leaves',json={'id':99,'employee_id':2,'start':'2026-11-02','end':'2026-11-02','kind':'comp_off'}).status_code==201
    assert client.post('/api/demands',json={'id':99,'brand_id':1,'process_id':3,'employee_ids':[],'staffing_by_weekday':[1,2]}).status_code==422
    assert client.put('/api/pods/1',json={'id':1,'name':'Pod','lead_employee_id':12}).status_code==409
