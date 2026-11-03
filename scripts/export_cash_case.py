"""Reproduce the explicitly hypothetical cash-timing example. No network or orders."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
def amount(value):
    return Decimal(str(value))

def formatted(value):
    return str(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def calculate(case):
    x=case['inputs']; fx=amount(x['fx_krw_per_usd'])
    if fx<=0: raise ValueError('positive FX required')
    first_krw_day=min(p['day'] for p in x['krw_obligations'])
    last_krw_day=max(p['day'] for p in x['krw_obligations'])
    first_usd_day=min(p['day'] for p in x['usd_obligations'])
    if x['receipt_day']>first_krw_day:
        raise ValueError('This example requires receipt by the first KRW obligation')
    if first_usd_day<=last_krw_day:
        raise ValueError('This example requires USD obligations after KRW obligations')
    opening=amount(x['starting_krw_cash']); floor=amount(x['minimum_krw_buffer'])
    due_krw=sum((amount(p['amount']) for p in x['krw_obligations']),Decimal(0))
    due_usd=sum((amount(p['amount']) for p in x['usd_obligations']),Decimal(0))
    total_usd=amount(x['starting_usd_bank_cash'])+amount(x['export_receipt_usd'])
    usd_for_krw=max(Decimal(0),(due_krw+floor-opening)/fx)
    headroom=total_usd-usd_for_krw-due_usd
    rows=[]
    for s in case['scenario_assumptions']:
        usable=amount(s['available_usd_before_day32'])
        delayed=amount(s['delayed_asset_usd_face'])
        if usable+delayed!=total_usd: raise ValueError('USD value must be conserved')
        if s['release_day'] is not None and s['release_day']<=last_krw_day:
            raise ValueError('This small example only models release after all KRW obligations')
        if s['release_day'] is not None and s['release_day']>=first_usd_day:
            raise ValueError('This example requires release before the USD obligation')
        cumul=Decimal(0); steps=[]
        for p in sorted(x['krw_obligations'],key=lambda p:p['day']):
            cumul+=amount(p['amount'])
            gap=max(Decimal(0),cumul+floor-opening-usable*fx)
            steps.append({'day':p['day'],'cumulative_krw_need_including_buffer':formatted(cumul+floor),'minimum_cumulative_bridge_krw':formatted(gap)})
        peak=max(Decimal(p['minimum_cumulative_bridge_krw']) for p in steps)
        rows.append({'id':s['id'],'schedule':steps,'peak_bridge_krw':formatted(peak)})
    return {'case_id':case['case_id'],'classification':case['classification'],'fx_is_assumption':True,'usd_needed_for_krw_payments_and_buffer':formatted(usd_for_krw),'usd_reserved_for_import':formatted(due_usd),'remaining_usd_after_listed_obligations_and_buffer':formatted(headroom),'scenarios':rows,'not_measured_performance':True}

if __name__=='__main__':
    case=json.loads((ROOT/'data/kyongnam_export_cash_case.json').read_text(encoding='utf-8'))
    print(json.dumps(calculate(case),ensure_ascii=False,indent=2))
