"""CP-SAT maximizes coverage first, then balances monthly workload."""
from calendar import monthrange
from collections import Counter
from datetime import date
from ortools.sat.python import cp_model

def dates(year,month):
    return [date(year,month,i).isoformat() for i in range(1,monthrange(year,month)[1]+1)]

def eligible(state,day,demand,employee):
    brand = next(b for b in state['brands'] if b['id']==demand['brand_id'])
    d = date.fromisoformat(day)
    reasons=[]
    if not employee['active']: reasons.append('inactive')
    if employee['id'] not in demand['employee_ids']: reasons.append('not assigned to demand')
    if employee['pod_id'] != brand['pod_id']: reasons.append('pod mismatch')
    if demand['process_id'] not in employee['process_ids']: reasons.append('process ineligible')
    if d.weekday()==employee['weekly_off']: reasons.append('weekly off')
    if d.weekday() not in brand['operating_weekdays'] or d.weekday() not in demand.get('operating_weekdays',list(range(7))): reasons.append('brand closed')
    if day in brand['holiday_dates']: reasons.append('brand holiday')
    if (brand['holidays_closed'] or demand.get('holidays_closed',False)) and any(h['day']==day for h in state['holidays']): reasons.append('company holiday')
    if any(l['employee_id']==employee['id'] and l['status']=='approved' and l['start']<=day<=l['end'] for l in state['leaves']): reasons.append('approved leave / comp-off / unavailability')
    return reasons

def operates(state,day,demand):
    brand=next(b for b in state['brands'] if b['id']==demand['brand_id'])
    return date.fromisoformat(day).weekday() in brand['operating_weekdays'] and date.fromisoformat(day).weekday() in demand.get('operating_weekdays',list(range(7))) and day not in brand['holiday_dates'] and not ((brand['holidays_closed'] or demand.get('holidays_closed',False)) and any(h['day']==day for h in state['holidays']))

def required(demand,day):
    values=demand.get('staffing_by_weekday',[])
    return values[date.fromisoformat(day).weekday()] if values else demand['min_staff']

def validate(state,year,month,slots):
    people={e['id']:e for e in state['employees']}; demands={d['id']:d for d in state['demands']}
    issues=[]; occupied=Counter(); workload=Counter(); coverage=Counter(); assigned_demands={}; assigned_brands={}; unique_shifts=set(); unique_slots=set()
    valid_dates=set(dates(year,month))
    for slot in slots:
        day,eid,did=slot['day'],slot['employee_id'],slot['demand_id']
        reasons=[]
        if day not in valid_dates: reasons.append('outside roster month')
        if eid not in people: reasons.append('unknown employee')
        if did not in demands: reasons.append('unknown demand')
        if eid in people and did in demands: reasons+=eligible(state,day,demands[did],people[eid])
        occupied[day,eid]+=1; assigned_demands.setdefault((day,eid),set()).add(did)
        if (day,eid,did) in unique_slots: reasons.append('duplicate assignment')
        unique_slots.add((day,eid,did))
        if did in demands: assigned_brands.setdefault((day,eid),set()).add(demands[did]['brand_id'])
        unique_shifts.add((day,eid))
        if reasons: issues.append({'type':'constraint','slot':slot,'reasons':reasons})
        else: coverage[day,did]+=1
    for day,eid in unique_shifts: workload[eid]+=1
    for (day,eid),brands in assigned_brands.items():
        if len(brands)>1: issues.append({'type':'double_booking','day':day,'employee_id':eid})
    for eid,n in workload.items():
        if eid in people and n>people[eid]['max_work_days']: issues.append({'type':'work_limit','employee_id':eid,'assigned':n,'limit':people[eid]['max_work_days']})
    shortages=[]
    for day in sorted(valid_dates):
        for did,dem in demands.items():
            if operates(state,day,dem) and coverage[day,did]<required(dem,day):
                candidates=[{'employee_id':eid,'reasons':eligible(state,day,dem,e)+(['already assigned to this demand'] if did in assigned_demands.get((day,eid),set()) else ['allocated elsewhere'] if occupied[day,eid] else [])+(['monthly work limit reached'] if workload[eid]>=e['max_work_days'] else [])} for eid,e in people.items() if eid in dem['employee_ids']]
                shortages.append({'type':'shortage','day':day,'demand_id':did,'required':required(dem,day),'filled':coverage[day,did],'missing':required(dem,day)-coverage[day,did],'candidates':candidates})
    return {'valid':not issues and not shortages,'conflicts':issues,'shortages':shortages,'workload':{str(eid):workload[eid] for eid in people},'coverage_required':sum(required(d,day) for day in valid_dates for d in demands.values() if operates(state,day,d)),'coverage_filled':sum(min(coverage[day,d['id']],required(d,day)) for day in valid_dates for d in demands.values() if operates(state,day,d))}

def generate(state,year,month):
    model=cp_model.CpModel(); variables={}; by_day={}; by_employee={}; by_demand={}; brand_shifts={}
    for day in dates(year,month):
        for dem in sorted(state['demands'],key=lambda d:d['id']):
            if not operates(state,day,dem): continue
            for e in sorted(state['employees'],key=lambda e:e['id']):
                if eligible(state,day,dem,e): continue
                key=(day,e['id'],dem['id']); v=model.new_bool_var('_'.join(map(str,key))); variables[key]=v
                shift_key=(day,e['id'],dem['brand_id'])
                if shift_key not in brand_shifts:
                    shift=model.new_bool_var('shift_'+str(shift_key)); brand_shifts[shift_key]=shift
                    by_day.setdefault((day,e['id']),[]).append(shift); by_employee.setdefault(e['id'],[]).append(shift)
                model.add(v<=brand_shifts[shift_key])
                by_demand.setdefault((day,dem['id']),[]).append(v)
            model.add(sum(by_demand.get((day,dem['id']),[]))<=required(dem,day))
    for (day,eid,bid),shift in brand_shifts.items():
        model.add(shift<=sum(v for (d,e,did),v in variables.items() if d==day and e==eid and next(x for x in state['demands'] if x['id']==did)['brand_id']==bid))
    for vs in by_day.values(): model.add(sum(vs)<=1)
    loads=[]
    for e in state['employees']:
        load=model.new_int_var(0,31,f"load{e['id']}"); model.add(load==sum(by_employee.get(e['id'],[]))); model.add(load<=e['max_work_days']); loads.append(load)
    high=model.new_int_var(0,31,'high'); low=model.new_int_var(0,31,'low')
    if loads: model.add_max_equality(high,loads); model.add_min_equality(low,loads)
    else: model.add(high==0); model.add(low==0)
    model.maximize(sum(variables.values()))
    solver=cp_model.CpSolver(); solver.parameters.num_search_workers=1; solver.parameters.random_seed=0; solver.parameters.max_time_in_seconds=10; solver.parameters.max_deterministic_time=2
    status=solver.solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE): raise ValueError('Solver could not produce a verified solution within the bounded search budget')
    coverage_optimal=status==cp_model.OPTIMAL
    filled=sum(solver.value(v) for v in variables.values())
    if coverage_optimal and loads:
        model.add(sum(variables.values())==filled)
        # A shift can cover several compatible processes; process coverage is not a day count.
        model.minimize(high-low)
        balanced=cp_model.CpSolver(); balanced.parameters.num_search_workers=1; balanced.parameters.random_seed=0
        balanced.parameters.max_time_in_seconds=10; balanced.parameters.max_deterministic_time=2
        balanced_status=balanced.solve(model)
        if balanced_status in (cp_model.OPTIMAL,cp_model.FEASIBLE): solver=balanced; status=balanced_status
        else: coverage_optimal=False
    slots=[{'day':day,'employee_id':eid,'demand_id':did} for (day,eid,did),v in variables.items() if solver.value(v)]
    result=validate(state,year,month,slots)
    return {'year':year,'month':month,'slots':slots,**result,'solver_status':solver.status_name(status),'optimal':coverage_optimal and status==cp_model.OPTIMAL,'coverage_optimal':coverage_optimal}
