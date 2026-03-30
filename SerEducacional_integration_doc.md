# Implementation Documentation: SerEducacional

**Generated on:** 2026-03-30
**Language:** EN

---

## Merchant Scope Summary

| Provider | Payment Method | Implemented Features |
|----------|---------------|---------------------|
| PAGARME | CARD | Experience, Card Type Accepted, Purchase, Refund, Cancel, Partial Refund, Multiple Refunds, External Refunds, Conciliations, Installments, Chargebacks, Network Tokens, Recurring, 3DS, Split, Soft Descriptor, ApplePay, GooglePay, ClickToPay |
| PAGARME | PIX | Experience, Card Type Accepted, Purchase, Refund, Cancel, Partial Refund, Multiple Refunds, External Refunds, Conciliations, Installments, Chargebacks, Network Tokens, Recurring, 3DS, Split, Soft Descriptor, ApplePay, GooglePay, ClickToPay |
| SAFRAPAY | CARD | Experience, Card Type Accepted, Purchase, Refund, Cancel, Partial Refund, Multiple Refunds, External Refunds, Conciliations, Installments, Chargebacks, Network Tokens, Recurring, 3DS, Split, Soft Descriptor, ApplePay, GooglePay, ClickToPay |

---

## Integration Steps

Follow these integration steps in sequential order to implement the required features for your payment integration.

### Master Integration Steps

These steps are required for all integrations regardless of which features are implemented.

#### Step 1: Essential setup and configuration steps required for all integrations.

**Documentation:** [https://docs.y.uno/docs/getting-started](https://docs.y.uno/docs/getting-started)

#### Step 2: Testing cards

**Documentation:** [https://docs.y.uno/docs/yuno-testing-gateway#442---card-detail](https://docs.y.uno/docs/yuno-testing-gateway#442---card-detail)

#### Step 3: Payment status and response codes

**Documentation:** [https://docs.y.uno/reference/payment](https://docs.y.uno/reference/payment)

### Feature-Specific Integration Steps

These steps correspond to the specific features implemented in your integration scope.

#### Step 4: Create payment documentation (Purchase)

**Documentation:** [https://docs.y.uno/reference/create-payment](https://docs.y.uno/reference/create-payment)

#### Step 5: Testing cards (Purchase)

**Documentation:** [https://docs.y.uno/docs/yuno-testing-gateway#442---card-detail](https://docs.y.uno/docs/yuno-testing-gateway#442---card-detail)

#### Step 6: Allows canceling authorized but not yet captured payments. Important for inventory management and customer service. (Cancel)

**Documentation:** [https://docs.y.uno/reference/cancel-payment](https://docs.y.uno/reference/cancel-payment)

#### Step 7: Supports full or partial refunds of completed payments. Critical for customer service and dispute resolution. (Refund)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 8: Enables recurring payment functionality for subscriptions and installments. Required for subscription-based business models. (Recurring)

**Documentation:** [https://docs.y.uno/docs/subscriptions](https://docs.y.uno/docs/subscriptions)

#### Step 9: Supports installment payments split across multiple charges. Popular in Latin American markets. (Installments)

**Documentation:** [https://docs.y.uno/reference/create-installments-plan](https://docs.y.uno/reference/create-installments-plan)

#### Step 10: 3D Secure authentication support for enhanced card payment security. Required for SCA compliance in Europe. (3DS)

**Documentation:** [https://docs.y.uno/docs/security-and-compliance/3d-secure](https://docs.y.uno/docs/security-and-compliance/3d-secure)

#### Step 11: Chargeback notification and management capabilities. Important for dispute resolution and merchant protection. (Chargeback)

**Documentation:** [https://docs.y.uno/docs/payouts-and-disputes/chargeback-management](https://docs.y.uno/docs/payouts-and-disputes/chargeback-management)

#### Step 12: Support for splitting payments between multiple recipients. Essential for marketplace and platform implementations. (Split)

**Documentation:** [https://docs.y.uno/docs/payment-features/split-payments-marketplace](https://docs.y.uno/docs/payment-features/split-payments-marketplace)

#### Step 13: Defines the integration experience type (SDK, API, Platform-specific). Determines implementation approach and technical requirements. (Experience)

**Documentation:** [https://docs.y.uno/docs/choose-the-right-integration-for-you](https://docs.y.uno/docs/choose-the-right-integration-for-you)

#### Step 14: Specifies accepted card types (Credit, Debit, Prepaid). Critical for payment method validation and user experience. (Card Type)

**Documentation:** [https://docs.y.uno/docs/cards](https://docs.y.uno/docs/cards)

#### Step 15: Supports partial refunds of completed payments. Essential for handling returns, damages, and customer service scenarios. (Partial Refund)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 16: Supports multiple refund operations against a single payment. Important for complex return and customer service scenarios. (Multiple Refunds)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 17: Support for refunds initiated outside of Yuno platform. Important for reconciliation and external system integration. (External Refunds)

**Documentation:** [https://docs.y.uno/reference/refund-payment](https://docs.y.uno/reference/refund-payment)

#### Step 18: Automated reconciliation and settlement reporting. Essential for financial operations and compliance. (Conciliations)

**Documentation:** [https://docs.y.uno/docs/reconciliations](https://docs.y.uno/docs/reconciliations)

#### Step 19: Support for card network tokenization (Visa, Mastercard tokens). Improves authorization rates and reduces fraud. (Network Tokens)

**Documentation:** [https://docs.y.uno/docs/network-tokens](https://docs.y.uno/docs/network-tokens)

#### Step 20: Identifies the target market segment for the payment provider. Affects available features and pricing models. (Market Segment)

**Documentation:** [https://docs.y.uno/reference/api-reference-overview](https://docs.y.uno/reference/api-reference-overview)

#### Step 21: Support for customizable merchant descriptors on customer statements. Important for brand recognition and chargeback prevention. (Soft Descriptor)

**Documentation:** [https://docs.y.uno/reference/create-payment](https://docs.y.uno/reference/create-payment)

#### Step 22: Apple Pay digital wallet integration. Provides seamless mobile payment experience for iOS users. (ApplePay)

**Documentation:** [https://docs.y.uno/docs/apple-pay](https://docs.y.uno/docs/apple-pay)

#### Step 23: Google Pay digital wallet integration. Enables fast and secure payments for Android and web users. (GooglePay)

**Documentation:** [https://docs.y.uno/docs/google-pay](https://docs.y.uno/docs/google-pay)

#### Step 24: Click to Pay functionality for streamlined checkout experience. Reduces cart abandonment through simplified payment flows. (ClickToPay)

**Documentation:** [https://docs.y.uno/docs/click-to-pay](https://docs.y.uno/docs/click-to-pay)

---

*This document was automatically generated from your implementation scope using /imp-doc-creator.*
