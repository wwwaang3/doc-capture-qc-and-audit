import unittest

from audit_qc.engine import LineItem, audit_invoice_vs_packing_list, evaluate_capture_quality


class TestTradeAuditAndCaptureQC(unittest.TestCase):
    def test_clean_invoice_and_packing_list_pass(self):
        inv = [LineItem("SKU-01", "Breaker 400A", "853620", 10, 125.50, 1255.00, 42.0, 45.0)]
        pack = [LineItem("SKU-01", "Breaker 400A", "853620", 10, 125.50, 1255.00, 42.0, 45.0)]
        report = audit_invoice_vs_packing_list("INV-2026-001", "USD", 1255.00, inv, pack, 45.0)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.discrepancies), 0)

    def test_catches_math_qty_weight_and_hs_errors(self):
        inv = [LineItem("SKU-02", "Switchgear Panel", "8537", 4, 500.0, 1950.0, 120.0, 130.0)]
        pack = [LineItem("SKU-02", "Switchgear Panel", "8537", 3, 500.0, 1950.0, 135.0, 130.0)]
        report = audit_invoice_vs_packing_list("INV-2026-002", "USD", 1950.0, inv, pack, 140.0)
        codes = {d.code for d in report.discrepancies}
        self.assertFalse(report.passed)
        self.assertIn("LINE_MATH_MISMATCH", codes)
        self.assertIn("INVOICE_TOTAL_MISMATCH", codes)
        self.assertIn("INVALID_HS_CODE", codes)
        self.assertIn("QTY_MISMATCH", codes)
        self.assertIn("NET_EXCEEDS_GROSS", codes)
        self.assertIn("GROSS_WEIGHT_MISMATCH", codes)

    def test_capture_qc_rejects_blurry_and_glare_frames(self):
        flat_glare = [[254 for _ in range(10)] for _ in range(10)]
        res = evaluate_capture_quality(flat_glare)
        self.assertFalse(res["acceptable"])
        self.assertGreaterEqual(len(res["guidance"]), 2)

    def test_capture_qc_accepts_sharp_well_lit_frame(self):
        sharp = [[180 if (r + c) % 2 == 0 else 100 for c in range(12)] for r in range(12)]
        res = evaluate_capture_quality(sharp)
        self.assertTrue(res["acceptable"])
        self.assertEqual(res["guidance"], [])


if __name__ == "__main__":
    unittest.main()
