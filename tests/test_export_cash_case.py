"""Check financial conservation and liquidity constraints in the teaching case."""
import importlib.util
import json
import unittest
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cash_case',ROOT/'scripts/export_cash_case.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CashTimingTests(unittest.TestCase):
    def setUp(self):
        self.case=json.loads((ROOT/'data/kyongnam_export_cash_case.json').read_text(encoding='utf-8'))

    def test_equal_asset_values_can_have_different_payment_gaps(self):
        result=module.calculate(self.case)
        rows={x['id']:x for x in result['scenarios']}
        self.assertEqual(rows['BANK']['peak_bridge_krw'],'0.00')
        self.assertEqual(rows['STABLECOIN-DELAY']['schedule'][0]['minimum_cumulative_bridge_krw'],'460000000.00')
        self.assertEqual(rows['STABLECOIN-DELAY']['peak_bridge_krw'],'760000000.00')
        self.assertEqual(rows['FUND-DELAY']['peak_bridge_krw'],'340000000.00')
        # KRW outflows, retained KRW, USD import and residual reconcile at assumed FX.
        residual=Decimal(result['remaining_usd_after_listed_obligations_and_buffer'])
        final_value=Decimal('100000000')+(Decimal('250000')+residual)*Decimal('1400')
        opening_value=Decimal('200000000')+Decimal('1100000')*Decimal('1400')
        self.assertLess(abs(final_value+Decimal('1000000000')-opening_value),Decimal('10'))

    def test_existing_cash_changes_gap_without_changing_token_format(self):
        self.case['inputs']['starting_krw_cash']='960000000'
        result=module.calculate(self.case)
        self.assertEqual(result['scenarios'][1]['peak_bridge_krw'],'0.00')

    def test_double_counted_asset_is_rejected(self):
        self.case['scenario_assumptions'][1]['available_usd_before_day32']='1100000'
        with self.assertRaisesRegex(ValueError,'conserved'):
            module.calculate(self.case)

    def test_unmodelled_redemption_timing_is_not_silently_assumed(self):
        self.case['scenario_assumptions'][1]['release_day']=33
        with self.assertRaisesRegex(ValueError,'release after'):
            module.calculate(self.case)

    def test_late_export_receipt_does_not_count_as_available_bank_cash(self):
        self.case['inputs']['receipt_day']=33
        with self.assertRaisesRegex(ValueError,'receipt by'):
            module.calculate(self.case)

    def test_redemption_after_usd_payment_cannot_satisfy_that_payment(self):
        self.case['scenario_assumptions'][1]['release_day']=45
        with self.assertRaisesRegex(ValueError,'release before'):
            module.calculate(self.case)

if __name__=='__main__':unittest.main()
