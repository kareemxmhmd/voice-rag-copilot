# NovaCart Q3 2026 Churn Analysis Report

**Document ID:** KB-04 | **Period:** July 1 – September 30, 2026 | **Published:** October 14, 2026 | **Owner:** Product Operations and Data | **Audience:** Internal

Plan prices and policies referenced here are defined in KB-01, KB-02, and KB-03.

## 1. Executive Summary

NovaCart ended Q3 with **116,412 active paid subscribers**, down 0.25% from 116,705 at the end of Q2. Pro and Enterprise grew while Basic shrank.

- Monthly churn was **6.4% for Basic** and **2.1% for Pro**.
- Of 6,840 exit-survey responses, **38% cited shipping delays in regional zones** as the main reason for leaving.
- In the Basic save-flow test, the **60-day pause beat the 30% discount** on 90-day retention: 71% versus 54% of acceptors still active.
- Trial-to-paid conversion was 34.8% blended.

## 2. Headline KPIs

### 2.1 Churn, Subscribers, and LTV by Tier

| Tier | Monthly churn (Q3 avg) | Active at Sept 30 | Average LTV |
|---|---|---|---|
| Basic ($19.00/mo) | **6.4%** | 84,300 | **$297** |
| Pro ($180.00/yr) | **2.1%** | 31,900 | **$714** |
| Enterprise (from $499.00/mo) | 0.8% (account churn) | 212 accounts (3,860 seats) | $108,500 per account |
| **Total paid active** | | **116,412** | |

Free-tier registered members (not counted as subscribers): 412,000.

### 2.2 Subscriber Movement

| Tier | Q2 close | Gross adds | Churned | Q3 close |
|---|---|---|---|---|
| Basic | 86,100 | 14,490 | 16,290 | 84,300 |
| Pro | 30,400 | 3,450 | 1,950 | 31,900 |
| Enterprise (accounts) | 205 | 12 | 5 | 212 |
| Total | 116,705 | 17,952 | 18,245 | 116,412 |

Paused subscribers are excluded from active counts and are not counted as churn until they cancel.

### 2.3 Trial-to-Paid Conversion

Trials that reached day 14 during Q3:

| Plan | Trials completed | Converted | Conversion rate |
|---|---|---|---|
| Basic | 24,000 | 9,168 | **38.2%** |
| Pro | 11,000 | 3,014 | **27.4%** |
| Blended | 35,000 | 12,182 | **34.8%** |

### 2.4 LTV Method

LTV = monthly revenue per subscriber ÷ monthly churn.

- Basic: $19.00 ÷ 0.064 = $297.
- Pro: $15.00 effective monthly ($180.00 ÷ 12) ÷ 0.021 = $714.
- Enterprise: about $868 average monthly revenue per account ÷ 0.008 = $108,500. The $868 reflects an average of 18.2 seats per account ($499.00 plus extra seats at $45.00).

## 3. Top 3 Churn Drivers

Source: exit surveys from churned Basic and Pro subscribers. There were 6,840 responses from 18,240 churned subscribers (a 37.5% response rate).

| Rank | Driver | Share of responses |
|---|---|---|
| 1 | Shipping delays in regional zones | **38%** (about 2,599) |
| 2 | Perceived price-to-value gap after the 14-day trial | **31%** (about 2,120) |
| 3 | Underutilization of Pro perks or unawareness of cashback and pause | **19%** (about 1,300) |
| | Other (support experience 5%, competitor 4%, unspecified 3%) | 12% |

### 3.1 Driver 1: Shipping Delays

| Zone | Standard on-time rate | Average actual Standard time | Promised | Late Express rate |
|---|---|---|---|---|
| Zone A | 94.2% | 3.9 business days | 3–5 | 1.9% |
| Zone B | 81.5% | 5.6 business days | 3–5 | 6.1% |
| Zone C | 63.0% | 8.9 business days | 6–8 | 14.7% |

Among exit-survey respondents who cited shipping, 61% were in Zone B, 27% in Zone C, and 12% in Zone A.

### 3.2 Driver 2: Price-to-Value Gap

- 64% of these respondents canceled within 45 days of their first paid charge.
- The gap is largest for Basic, where the $19.00 monthly price is paid on top of the same free-shipping threshold ($75.00) as Free.

### 3.3 Driver 3: Underutilization

Among respondents citing this driver:
- 62% had redeemed $0 of NovaCash.
- 71% did not know the 60-day pause existed.

## 4. Retention Campaign Impact

### 4.1 Basic: 30% Offer vs. 60-Day Pause (A/B Test, July 15 – Sept 30)

Basic members in the cancel flow were randomly split, 10,000 per arm. "Active at day 90" is measured 90 days after accepting.

| Metric | 30% offer ($13.30 for 2 months) | 60-day pause |
|---|---|---|
| Accepted | 2,100 (21.0%) | 1,800 (18.0%) |
| Active at day 90 | 1,134 (54.0%) | 1,278 (71.0%) |
| Net saved per 10,000 shown | 1,134 (11.3%) | 1,278 (12.8%) |
| Direct discount cost | $23,940 ($11.40 per acceptor) | $0 |
| Cost per retained subscriber | $21.11 | $0 |
| Revenue timing | Reduced revenue for 2 cycles | No revenue for 60 days, then $19.00 resumes |

### 4.2 Pro: Pause Offer

Pro cancel flows show the pause only.

| Metric | Result |
|---|---|
| Shown | 4,200 |
| Accepted | 1,092 (26.0%) |
| Active at day 90 | 852 (78.0%) |

**Takeaway:** The discount wins on acceptance. The pause wins on retention and cost, and works especially well for Pro.

## 5. Actionable Recommendations for Q4

| # | Recommendation | Owner | Target |
|---|---|---|---|
| 1 | Fix Zone B and C delivery performance before Black Friday (Nov 27, 2026): add a second regional carrier in Zone B and proactive delay notices. Propose a $10.00 NovaCash credit for late Zone B and C orders on Free and Basic, matching the Pro/Enterprise credit | Fulfillment | Zone B on-time ≥ 90%, Zone C ≥ 75% by Dec 31 |
| 2 | Test pause-first for Basic in the cancel flow | Membership Product | Net saved at day 90 above 12.8% |
| 3 | Add value-recap content to the day-10 and day-12 trial reminders | Lifecycle Marketing | Conversion: Basic ≥ 42%, Pro ≥ 30% |
| 4 | Add a 30-day onboarding checklist covering NovaCash, early access, and pause | Product | Driver 3 share from 19% to ≤ 14% |
| 5 | Test a "savings so far" meter in the cart and account page. No list-price changes | Growth | Driver 2 share from 31% to ≤ 26% |
| 6 | Track qualifying perk orders and 7-day refund requests as standard dashboard metrics | Data | Live by Nov 30 |

**Q4 churn targets:** Basic ≤ 5.5% per month, Pro ≤ 1.8% per month.

## 6. Definitions

- **Monthly churn:** subscribers whose paid access ended in the month ÷ active paid subscribers at month start. For Pro this includes non-renewals and refund-based cancellations.
- **Account churn (Enterprise):** accounts lost ÷ opening accounts, averaged monthly.
- **Gross adds:** all new paid subscriptions, including trial conversions, direct sign-ups, upgrades from Free, and reactivations.