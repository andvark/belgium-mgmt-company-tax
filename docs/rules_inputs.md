# Rule inputs

Last updated 15 November 2026 after the project owner's reply.

## How to read the status column

| status | meaning |
|---|---|
| **checked** | confirmed by me from a primary or official statistical source reachable from this session |
| **supplied** | provided by the project owner with official citations (fin.belgium.be, ejustice, lachambre, socialsecurity.be); **the cited primary pages could not be opened from this session** (FPS Finance and FPS Economy pages return an anti-bot challenge; the ONSS URL returned 404), so I have not independently confirmed them |
| **scenario** | a reported negotiating position, not law and not a published rule; modelled as an assumption and varied |
| **open** | genuinely undecided or unavailable |

The anti-bot challenge was not circumvented. Where a value drives a headline result, it should be confirmed by someone able to read the primary page (list in section F).

## A. Segment definitions (decided by the project owner)

| segment | definition | which proposals touch it |
|---|---|---|
| **S0** | BV/SRL with **zero employees** | P1 (reduced corporate rate withdrawn) |
| **S1** | S0 **and** a single director **and** a single client | P1 and P3 (reduced dividend regimes withdrawn); P2 depends on payroll, so also S0 and others |

S1 is a subset of S0 and S0 is far larger than the "management company" label suggests (see counts, section E). Both are reported.

Alternatives modelled for the same person: employee, sole trader (natural person), BV owner. Horizon 2026-2040 with calendar-year policy start dates (2027, 2028).

## B. Current rules, income earned in 2026 (assessment year 2027)

| item | value | status |
|---|---|---|
| Personal income tax brackets | up to EUR 16,720: 25%; 16,720-29,510: 40%; 29,510-51,070: 45%; above 51,070: 50% | supplied (fin.belgium.be) |
| Basic tax-free allowance | **EUR 11,550** for income earned in 2026 (assessment year 2027); EUR 10,910 for income earned in 2025 (assessment year 2026) | supplied; resolves the earlier conflict (the figures use different year labels; a guide found earlier labelled the 2025-income figure as "2026") |
| How the allowance applies | brackets are applied to taxable income, then **EUR 2,887.50 (25% of 11,550)** is subtracted from the tax, floored at zero | supplied. **The current `belgium_abm` engine deducts the allowance from income before the brackets: this must be changed** |
| Municipal surcharge | **7.2% of personal income tax** as a national proxy (published weighted estimate for assessment year 2024; varies by municipality) | supplied (Statbel viz) |
| Employee social contributions | **13.07%** of gross pay | supplied (ONSS); URL not reachable |
| Employer social contributions | **25%** of gross pay (private for-profit benchmark) | supplied; employer reductions, special contributions and the employee work bonus change the actual cost: open |
| Employee professional expenses | deductible; lump-sum amounts | **open** (needed for the employee comparison) |
| Self-employed contributions (main occupation) | 20.5% up to EUR 75,024.54; 14.16% up to EUR 110,562.42; minimum EUR 890.42 per quarter before fund fees | supplied earlier; treatment above the second ceiling **open** |
| Company annual contribution | EUR 409.30 or EUR 1,022.38 (by 2024 balance-sheet total) | supplied earlier |
| Corporate tax | 25%; 20% on first EUR 100,000 for qualifying small companies | supplied earlier |
| Condition for the reduced rate | director remuneration at least EUR 51,000 (indexed from 45,000) for a calendar-year company; test starts in the fifth taxable period; lower pay can qualify if it covers taxable profit; reduced rate lost if flat-rate benefits in kind exceed 20% of total director pay | supplied earlier |
| VAT | 21%; small-business exemption up to EUR 25,000 turnover | supplied; same in all arrangements, excluded from the comparison |

## C. Dividend, liquidation and exit routes (current rules as supplied)

| route | treatment | status |
|---|---|---|
| Ordinary dividend | 30% withholding | supplied earlier |
| VVPRbis dividend | 18% since 1 July 2026 (was 15%) | supplied earlier |
| Liquidation reserve distributed as a dividend after the three-year wait | 10% levy at creation + 9.8% withholding = effective 18% | supplied earlier |
| **Ordinary liquidation surplus** | generally **30%** withholding on the surplus above fiscal paid-up capital, subject to exemptions | supplied |
| **Qualifying liquidation reserve paid out on actual liquidation** | the 10% levy paid at creation remains; **no additional withholding** generally. A 2026 anti-abuse rule can make the payout taxable if the recipient becomes a director of a company with the same or similar activity within three years (statutory defence exists) | supplied (law of 30 May 2026, art. 13) |
| **Private sale of BV shares** | gains taxable from 1 January 2026 (law of 6 April 2026): 10% after the annual exemption; for owners with at least 20% selling to an independent buyer, a substantial-shareholding regime exempts the first EUR 1 million of gains over five taxable periods, then 1.25%, 2.5%, 5%, 10%; other buyers have separate rates; shares held before 2026 start from their 31 December 2025 value | supplied. An earlier search snippet described a capital gains tax as prepared but stalled; the owner's source says it applies from 1 January 2026: **to confirm** |

**Modelling consequence:** two very different "lump sum" exits exist for an owner who retains profits: a liquidation-reserve payout on liquidation at about 10% in total, and a dividend after three years at about 18%. For a one-person consultancy a share sale to an independent buyer is rarely realistic, so liquidation and dividend are the relevant exits. The owner strategy must include **the choice of exit route and its timing**.

## D. The three proposals (draft; not law as of 15 November 2026)

| # | proposal | what is known | status |
|---|---|---|---|
| P1 | Reduced corporate rate withdrawn for companies without employees | 20% -> 25% on the first EUR 100,000 of taxable profit; the wording quoted in Parliament says "companies with no employees". **No published test** for minimum hours, months employed, or how relatives, students, flexi-job workers or agency staff count. The ordinary part-time minimum (one tenth of full-time hours from 1 June 2026) is employment law, not the tax test | rate change supplied; employee test **open** |
| P2 | Reduced dividend regimes tied to payroll | total director and employee remuneration of **2x or 3x the dividend** reported as negotiating options (cap on dividends relative to payroll; e.g. EUR 60,000 payroll implies EUR 30,000 or EUR 20,000 dividends); payroll period and treatment of a payout above the limit unknown; proposed start 1 January 2028 | **scenario**; source quality low (see below) |
| P3 | Reduced dividend regimes (VVPRbis, liquidation reserve) withdrawn for long-term single-client companies | one director working almost exclusively for the same client for several years; new amounts from 2028; no exact percentage, number of years, or treatment of intermediaries and related clients. A **90%** figure appeared in a report of a later negotiating version about companies without staff | **scenario**; 90% reached only through a repost |

**Source-quality note.** The excerpts for P2 and P3 and the later 15 November negotiating details are cited from Reddit threads (a community
forum reposting a published draft excerpt and press reports). Treat them as pointers, not as sources: the draft text itself (or reliable
press reports quoting it) should replace them before any result is presented as being about "the proposal". Until then:

- run P2 at 2x and 3x as separate scenarios;
- run P3 over a grid of client thresholds (for example 70%, 80%, 90%, 100%) and lookback periods (for example 3, 5 years);
- leave the effect of a small or family hire under P1 as a scenario (take-up and cost swept).

Government's projected revenue: EUR 300m (2027); EUR 450m a year (2028, 2029); methodology unknown (supplied).

## E. Counts for calibration

| item | value | status |
|---|---|---|
| VAT-registered enterprises with **no employees**, end 2024, all legal forms | **997,481** (Flanders 635,004; Brussels 100,244; Wallonia 246,015; foreign 16,202) | **checked** (Statbel BeStat, view `7f159942...`) |
| Private limited companies (BV/SRL), VAT-registered, 2024, all sizes | 477,126 (Flanders 308,042; Brussels 61,728; Wallonia 107,356) | **checked** (Statbel BeStat legal-form view); consistent with the 476,914 BV/SRL SMEs supplied from FPS Economy |
| Share of BV/SRL SMEs with no employees | 73.7%, implying about **351,000** zero-employee BV/SRL SMEs (476,914 x 0.737 = 351,500) | supplied (FPS Economy page not reachable); arithmetic checked, share **unverified** |
| Zero-employee enterprises, business economy, 2024 (Eurostat) | 729,925; births 67,369; deaths 50,325 | checked (different definition from the Statbel VAT count) |
| Single-director and one-client shares within S0 | - | **open**; S1 cannot yet be sized |
| Earlier claim of "more than 80,000 single-person management companies" | - | unverified; far below 351,000, consistent with S1 being a small part of S0 |

## F. What still needs confirmation by someone who can open the primary pages

1. FPS Finance personal income tax rates page (brackets, EUR 11,550, EUR 2,887.50 reduction, professional-expense lump sums).
2. FPS Economy SME-by-legal-form page (476,914 and 73.7%) or the Statbel 2025 legal-form by employer-class download.
3. ONSS employer contribution page (13.07%, 25%, reductions, work bonus). The URL supplied returned 404.
4. The law of 30 May 2026 (liquidation reserve, art. 13) and the law of 6 April 2026 (capital gains on share sales).
5. The draft text for P2 and P3, replacing the Reddit-sourced excerpts.

## G. Still missing

- employee professional-expense lump sums, employer reductions and work bonus (for the employee comparator);
- treatment of self-employed contributions above the second ceiling;
- the share of S0 with a single director and one client;
- the distribution of director pay and retained profits in S0 (form 281.20 and NBB annual accounts give routes, no public distribution found);
- the employee definition for P1.
