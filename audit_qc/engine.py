"""Trade Document Cross-Audit & Image Capture Quality Gate Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass
class LineItem:
    sku: str
    description: str
    hs_code: str
    quantity: int
    unit_price: float
    line_total: float
    net_weight_kg: float
    gross_weight_kg: float


@dataclass
class Discrepancy:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class AuditReport:
    document_ref: str
    passed: bool
    discrepancies: List[Discrepancy] = field(default_factory=list)
    invoice_declared_total: float = 0.0
    invoice_computed_total: float = 0.0


def audit_invoice_vs_packing_list(
    document_ref: str,
    invoice_currency: str,
    invoice_declared_total: float,
    invoice_items: Sequence[LineItem],
    packing_items: Sequence[LineItem],
    declared_gross_weight_kg: float,
    weight_tolerance_kg: float = 0.5,
    amount_tolerance: float = 0.02,
) -> AuditReport:
    issues: List[Discrepancy] = []
    if not invoice_currency or len(invoice_currency.strip()) != 3:
        issues.append(Discrepancy("HIGH", "INVALID_CURRENCY", "currency", f"Invalid currency: {invoice_currency!r}"))

    computed_total = 0.0
    inv_by_sku: Dict[str, LineItem] = {}
    for item in invoice_items:
        inv_by_sku[item.sku] = item
        expected_line = round(item.quantity * item.unit_price, 2)
        computed_total += expected_line
        if abs(expected_line - item.line_total) > amount_tolerance:
            issues.append(Discrepancy("HIGH", "LINE_MATH_MISMATCH", f"invoice.{item.sku}.line_total", f"SKU {item.sku}: expected {expected_line:.2f}, got {item.line_total:.2f}"))
        if not item.hs_code or len(item.hs_code.replace(".", "").strip()) < 6:
            issues.append(Discrepancy("MEDIUM", "INVALID_HS_CODE", f"invoice.{item.sku}.hs_code", f"SKU {item.sku}: invalid HS code {item.hs_code!r}"))

    computed_total = round(computed_total, 2)
    if abs(computed_total - invoice_declared_total) > amount_tolerance:
        issues.append(Discrepancy("HIGH", "INVOICE_TOTAL_MISMATCH", "invoice.total", f"Declared {invoice_declared_total:.2f} != computed {computed_total:.2f}"))

    pack_by_sku = {p.sku: p for p in packing_items}
    for sku, inv_item in inv_by_sku.items():
        pack_item = pack_by_sku.get(sku)
        if pack_item is None:
            issues.append(Discrepancy("HIGH", "MISSING_ON_PACKING_LIST", f"packing.{sku}", f"SKU {sku} missing on packing list"))
            continue
        if pack_item.quantity != inv_item.quantity:
            issues.append(Discrepancy("HIGH", "QTY_MISMATCH", f"packing.{sku}.quantity", f"SKU {sku}: invoice {inv_item.quantity} != packing {pack_item.quantity}"))
        if pack_item.net_weight_kg > pack_item.gross_weight_kg:
            issues.append(Discrepancy("HIGH", "NET_EXCEEDS_GROSS", f"packing.{sku}.weight", f"SKU {sku}: net {pack_item.net_weight_kg} > gross {pack_item.gross_weight_kg}"))

    for sku in pack_by_sku:
        if sku not in inv_by_sku:
            issues.append(Discrepancy("HIGH", "EXTRA_PACKING_SKU", f"packing.{sku}", f"SKU {sku} on packing list not billed on invoice"))

    summed_gross = round(sum(p.gross_weight_kg for p in packing_items), 2)
    if abs(summed_gross - declared_gross_weight_kg) > weight_tolerance_kg:
        issues.append(Discrepancy("MEDIUM", "GROSS_WEIGHT_MISMATCH", "packing.declared_gross_weight_kg", f"Declared {declared_gross_weight_kg:.2f} kg != sum {summed_gross:.2f} kg"))

    return AuditReport(document_ref=document_ref, passed=len(issues) == 0, discrepancies=issues, invoice_declared_total=invoice_declared_total, invoice_computed_total=computed_total)


def evaluate_capture_quality(
    gray_matrix: Sequence[Sequence[int]],
    min_sharpness: float = 12.0,
    max_glare_ratio: float = 0.08,
    min_mean_luma: float = 45.0,
    max_mean_luma: float = 235.0,
) -> Dict[str, object]:
    rows = len(gray_matrix)
    cols = len(gray_matrix[0]) if rows else 0
    if rows < 3 or cols < 3:
        return {"acceptable": False, "guidance": ["Image resolution too small."]}
    total_pixels = rows * cols
    luma_sum = sum(px for row in gray_matrix for px in row)
    glare_pixels = sum(1 for row in gray_matrix for px in row if px >= 250)
    mean_luma = luma_sum / total_pixels
    glare_ratio = glare_pixels / total_pixels
    lap_vals = [
        float(gray_matrix[r - 1][c] + gray_matrix[r + 1][c] + gray_matrix[r][c - 1] + gray_matrix[r][c + 1] - 4 * gray_matrix[r][c])
        for r in range(1, rows - 1) for c in range(1, cols - 1)
    ]
    mean_lap = sum(lap_vals) / len(lap_vals)
    sharpness_var = sum((v - mean_lap) ** 2 for v in lap_vals) / len(lap_vals)
    guidance: List[str] = []
    if sharpness_var < min_sharpness:
        guidance.append("Image appears out of focus — hold steady and tap to refocus.")
    if glare_ratio > max_glare_ratio:
        guidance.append("Strong specular glare detected — tilt camera slightly to reduce reflection.")
    if mean_luma < min_mean_luma:
        guidance.append("Image is too dark — move to brighter, even lighting.")
    elif mean_luma > max_mean_luma:
        guidance.append("Image is overexposed — reduce direct backlight.")
    return {"acceptable": len(guidance) == 0, "metrics": {"mean_luma": round(mean_luma, 2), "glare_ratio": round(glare_ratio, 4), "laplacian_variance": round(sharpness_var, 2)}, "guidance": guidance}
