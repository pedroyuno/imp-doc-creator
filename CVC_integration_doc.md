# Implementation Documentation: CVC

**Generated on:** 2026-03-31
**Language:** EN

---

## Merchant Scope Summary

| Provider | Payment Method | Implemented Features |
|----------|---------------|---------------------|
| GETNET | CARD | Experience, Card Type Accepted, Authorize, Capture, Purchase, Refund, Cancel, Partial Refund, Multiple Refunds, Installments, Chargebacks, 3DS, Soft Descriptor |
| REDE | CARD | Experience, Card Type Accepted, Authorize, Capture, Purchase, Refund, Cancel, Partial Refund, Multiple Refunds, Installments, Chargebacks, 3DS, Soft Descriptor |
| CIELO | CARD | Experience, Card Type Accepted, Authorize, Capture, Purchase, Refund, Cancel, Partial Refund, Multiple Refunds, Installments, Chargebacks, 3DS, Soft Descriptor |

---

## Integration Steps

Follow these integration steps in sequential order to implement the required features for your payment integration.

### Master Integration Steps

These steps are required for all integrations regardless of which features are implemented.

#### Step 1: Set up your Yuno account and API keys

**Documentation:** [https://docs.y.uno/docs/getting-started](https://docs.y.uno/docs/getting-started)

#### Step 2: Get test cards for sandbox testing

**Documentation:** [https://docs.y.uno/docs/yuno-testing-gateway#442---card-detail](https://docs.y.uno/docs/yuno-testing-gateway#442---card-detail)

#### Step 3: Review payment status codes and responses

**Documentation:** [https://docs.y.uno/reference/payment](https://docs.y.uno/reference/payment)

### Feature-Specific Integration Steps

These steps correspond to the specific features implemented in your integration scope.

#### Step 4: Create a one-step payment (Purchase)

**Documentation:** [https://docs.y.uno/reference/create-payment](https://docs.y.uno/reference/create-payment)

#### Step 5: Authorize a payment without capturing (Authorize)

**Documentation:** [https://docs.y.uno/reference/authorize-payment](https://docs.y.uno/reference/authorize-payment)

#### Step 6: Capture a previously authorized payment (Capture)

**Documentation:** [https://docs.y.uno/reference/capture-authorization](https://docs.y.uno/reference/capture-authorization)

#### Step 7: Cancel an authorized payment before capture (Cancel)

**Documentation:** [https://docs.y.uno/reference/cancel-payment](https://docs.y.uno/reference/cancel-payment)

#### Step 8: Refund a completed payment, full or partial (Refund)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 9: Create an installment plan for split charges (Installments)

**Documentation:** [https://docs.y.uno/reference/create-installments-plan](https://docs.y.uno/reference/create-installments-plan)

#### Step 10: Configure 3D Secure authentication (3DS)

**Documentation:** [https://docs.y.uno/docs/security-and-compliance/3d-secure](https://docs.y.uno/docs/security-and-compliance/3d-secure)

#### Step 11: Handle chargeback notifications and submit evidence (Chargeback)

**Documentation:** [https://docs.y.uno/docs/payouts-and-disputes/chargeback-management](https://docs.y.uno/docs/payouts-and-disputes/chargeback-management)

#### Step 12: Choose your integration type - SDK, API, or Checkout (Experience)

**Documentation:** [https://docs.y.uno/docs/choose-the-right-integration-for-you](https://docs.y.uno/docs/choose-the-right-integration-for-you)

#### Step 13: Configure accepted card types - Credit, Debit, Prepaid (Card Type)

**Documentation:** [https://docs.y.uno/docs/cards](https://docs.y.uno/docs/cards)

#### Step 14: Refund a partial amount from a completed payment (Partial Refund)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 15: Perform multiple refunds against one payment (Multiple Refunds)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 16: Review API reference for your market segment (Market Segment)

**Documentation:** [https://docs.y.uno/reference/api-reference-overview](https://docs.y.uno/reference/api-reference-overview)

#### Step 17: Set a custom statement descriptor for payments (Soft Descriptor)

**Documentation:** [https://docs.y.uno/reference/create-payment](https://docs.y.uno/reference/create-payment)

---

*This document was automatically generated from your implementation scope using /imp-doc-creator.*
