# Trade Document Cross-Audit & Image Capture Quality Gate

**Maintained by Lingkefa Intelligent Technology (Ningbo) Co., Ltd. — AMD Edge AI Ecosystem Partner**

Zero-dependency Python 3.9+ reference implementation showcasing the deterministic verification layer behind our on-premise document review pipelines (**550 multi-document cases/day, 40s/case, 95% field accuracy, 80% less manual review**).

## What It Does

1. **Commercial Invoice vs. Packing List Cross-Audit (`audit_invoice_vs_packing_list`)**
   - Catches line-item math errors (`qty * unit_price != line_total`) and invoice total discrepancies
   - Flags malformed ISO currency codes and short (<6-digit) HS codes
   - Reconciles invoice SKUs & quantities against packing lists (missing/extra SKUs, quantity mismatches)
   - Detects impossible net-vs-gross weight inversions and gross weight summation mismatches
2. **Pre-OCR / Camera Image Capture Quality Gate (`evaluate_capture_quality`)**
   - Discrete 4-neighbor Laplacian variance focus/blur scoring
   - Specular glare pixel saturation ratio detection
   - Mean luminance underexposure / overexposure checks
   - Actionable real-time retake guidance messages for mobile & scanner operators

## Run Unit Tests

```bash
python3 -m unittest discover -s tests -v
```

## Contact & Custom On-Premise Pilots

- **Free 48-Hour Benchmark**: Send 3 redacted sample PDFs (commercial invoices, packing lists, customs paperwork) or 1 single-line electrical diagram — we return structured Excel output + discrepancy report within 48 hours at zero cost.
- **Contact**: Rufa Wang — Co-Founder, Lingkefa Intelligent Technology (Ningbo) Co., Ltd.
- **Email**: `wwwaang3@gmail.com` | **WhatsApp**: `+86 187 5831 1950`
