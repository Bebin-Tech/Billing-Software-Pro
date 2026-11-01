"""Decimal-only domestic standard supply calculator, version 1.

Caller must establish the legal place of supply. Special transactions need a
qualified rule review; a state code alone is not a place-of-supply determination.
"""
from decimal import Decimal, ROUND_HALF_UP

D = Decimal


def money(value):
    result=D(value).quantize(D('0.01'), rounding=ROUND_HALF_UP)
    if abs(result)>D('9999999999999999.99'):
        raise ValueError('Amount exceeds DECIMAL(18,2) storage capacity')
    return result


def calculate(items, seller_state, supply_state, rule='domestic_standard', reverse_charge=False):
    if rule not in ('domestic_standard', 'sez'):
        raise ValueError('Unsupported supply rule')
    interstate = rule == 'sez' or seller_state != supply_state
    rows = []
    for item in items:
        rate = D(item['gst_rate'])
        gross = D(item['price']) * D(item['quantity'])
        discounted = gross * (1 - D(item.get('discount_percent', 0)) / 100)
        taxable = money(discounted / (1 + rate / 100) if item.get('inclusive') else discounted)
        # RCM liability is reported separately and not collected from customer.
        tax = money(taxable * rate / 100)
        cgst = money(tax / 2) if not interstate else D(0)
        sgst = tax - cgst if not interstate else D(0)
        rows.append({**item, 'taxable': str(taxable), 'cgst': str(cgst), 'sgst': str(sgst),
                     'igst': str(tax if interstate else D(0)), 'tax': str(tax),
                     'total': str(taxable + (D(0) if reverse_charge else tax))})
    taxable = sum((D(r['taxable']) for r in rows), D(0))
    tax = sum((D(r['tax']) for r in rows), D(0))
    return {'rule_version': 'domestic-v1', 'supply_rule': rule, 'reverse_charge': reverse_charge,
            'interstate': interstate, 'items': rows, 'taxable': str(money(taxable)),
            'tax': str(money(tax)), 'total': str(money(taxable + (D(0) if reverse_charge else tax)))}
